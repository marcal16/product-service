import logging
import asyncio
from product_service.dependencies.session import AsyncSessionLocal
from product_service.srv.events_srv import process_job, recover_stucked_jobs
from product_service.core.logs import setup_logging

logger = logging.getLogger(__name__)


async def worker_loop():
    logger.info("Worker started")

    while True:
        async with AsyncSessionLocal() as session:
            await recover_stucked_jobs(session)
            status = await process_job(session)

        if not status:
            logger.info("No jobs found, pending")
            await asyncio.sleep(10)


# for tests
async def single_worker():
    async with AsyncSessionLocal() as session:
        return await process_job(session)


def main():
    setup_logging()
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
