import logging
import multiprocessing
import os
from queue import Empty
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from Worker.worker import run_worker

app = FastAPI()
logger = logging.getLogger("ozon.api")

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

PROCESS_TIMEOUT_SEC = int(os.getenv("OZON_PROCESS_TIMEOUT_SEC", "900"))


class LinkSettings(BaseModel):
    url: str
    limit: Optional[int] = Field(default=None, ge=1, le=1000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("url must start with http or https")
        if not parsed.netloc:
            raise ValueError("url must contain a valid host")
        return value


class ScrapeRequest(BaseModel):
    links_settings: List[LinkSettings] = Field(min_length=1, max_length=50)


def worker_entry(queue, links_settings):
    try:
        result = run_worker(links_settings)
        queue.put(result)
    except Exception as e:
        logger.exception("Unhandled error in worker_entry: %s", e)
        queue.put({"error": str(e), "data": []})


@app.post("/scrape")
async def scrape_api(req: ScrapeRequest):
    links_settings = [item.model_dump() for item in req.links_settings]
    logger.info("Incoming scrape request. links=%s", len(links_settings))

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=worker_entry,
        args=(queue, links_settings),
    )

    process.start()
    try:
        # Important: read from Queue before join() to avoid deadlock on large payloads.
        result = queue.get(timeout=PROCESS_TIMEOUT_SEC)
    except Empty:
        if process.is_alive():
            process.terminate()
            process.join()
            logger.error("Scrape process timeout after %ss", PROCESS_TIMEOUT_SEC)
            raise HTTPException(
                status_code=504,
                detail=f"Scrape timed out after {PROCESS_TIMEOUT_SEC} seconds",
            )
        logger.error("Scrape process finished without result in queue")
        raise HTTPException(
            status_code=500,
            detail="Worker finished without returning a result",
        )
    finally:
        process.join(timeout=5)

    if process.is_alive():
        process.terminate()
        process.join()
        logger.error("Scrape process did not exit cleanly after result")
        raise HTTPException(
            status_code=500,
            detail="Scrape process did not exit cleanly",
        )

    if process.exitcode not in (0, None):
        logger.error("Scrape process crashed. exit_code=%s", process.exitcode)
        raise HTTPException(
            status_code=500,
            detail=f"Scrape process failed with exit code {process.exitcode}",
        )

    if isinstance(result, dict) and result.get("error"):
        logger.warning("Scrape finished with worker error: %s", result.get("error"))
    else:
        logger.info("Scrape finished successfully")

    return result