import asyncio
import logging
from Parser.scraper2 import OzonScraper

logger = logging.getLogger("ozon.worker")

def run_worker(links_settings):
    try:
        logger.info("Worker started. links=%s", len(links_settings))
        scraper = OzonScraper()

        result = asyncio.run(scraper.scrape(links_settings))

        logger.info("Worker done. items=%s", len(result))

        return {
            "count": len(result),
            "data": result
        }

    except Exception as e:
        logger.exception("Worker error: %s", e)

        return {
            "error": str(e),
            "data": []
        }