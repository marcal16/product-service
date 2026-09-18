import logging
import time
from product_service.repos.events_repo import get_job, update_job_status, recover_stucked_jobs_repo
from product_service.db.models.events import EventTypesEnum

logger = logging.getLogger(__name__)


async def recover_stucked_jobs(session):
    await recover_stucked_jobs_repo(session)


async def process_job(session, error: bool = False):

    try:
        job = await get_job(session)

        if job is None:
            return None

        try:
            make_job(job.payload, error)
            await update_job_status(session, job, EventTypesEnum.PROCESSED)
            logger.info("Job is done")
            return job.status
        except Exception as e:
            await update_job_status(session, job, EventTypesEnum.FAILED)
            logger.exception(str(e))
            return job.status

    except Exception as e:
        await session.rollback()
        logger.exception(str(e))


def make_job(payload, error):

    if error:
        raise Exception

    time.sleep(2)
    logger.info(f"Order with ID {payload['id']} and number of items {payload['items_number']} is ready")
