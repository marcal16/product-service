from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from product_service.db.models.events import OutboxEvents, EventTypesEnum
from sqlalchemy.ext.asyncio import AsyncSession


def add_event(session: AsyncSession, payload: dict):

    event = OutboxEvents(**payload, attempts=0, status=EventTypesEnum.PENDING)

    session.add(event)


async def get_job(session: AsyncSession):

    stmt = (
        select(OutboxEvents)
        .where(OutboxEvents.status.in_([EventTypesEnum.PENDING, EventTypesEnum.FAILED]))
        .order_by(OutboxEvents.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    job = await session.scalar(stmt)
    if not job:
        return None
    job.processed_at = datetime.now(timezone.utc)
    job.attempts = job.attempts + 1 if job.attempts else 1
    await session.commit()
    await session.refresh(job)

    return job


async def update_job_status(session: AsyncSession, job: OutboxEvents, status: EventTypesEnum):

    job.status = status
    if status == EventTypesEnum.FAILED:
        job.last_error = datetime.now(timezone.utc)
    await session.commit()


# Made for tests and checks
async def get_jobs(session: AsyncSession, id: int = None):

    stmt = select(OutboxEvents).order_by(OutboxEvents.id.asc())
    if id:
        stmt = stmt.where(OutboxEvents.id == id)
    else:
        stmt = stmt.where(OutboxEvents.status == EventTypesEnum.PENDING)

    res = await session.scalars(stmt)
    return res.all()


async def recover_stucked_jobs_repo(session: AsyncSession):

    TIMEOUT = timedelta(minutes=5)

    stmt = (
        select(OutboxEvents)
        .where(
            OutboxEvents.status
            == EventTypesEnum.PROCESSING & (datetime.now(timezone.utc) - OutboxEvents.processed_at > TIMEOUT)
        )
        .order_by(OutboxEvents.created_at.asc())
        .with_for_update(skip_locked=True)
    )

    res = await session.scalars(stmt)
    jobs = res.all()

    if not jobs:
        return

    for job in jobs:
        job.status = EventTypesEnum.FAILED
    await session.commit()
