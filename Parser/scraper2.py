import asyncio
import logging
from Utils.export import save_json,  save_csv, save_xlsx
from Utils.human import human_scroll

from cloakbrowser import launch_async

logger = logging.getLogger("ozon.scraper")


class OzonScraper:
    def __init__(self, headless=False, max_concurrent=3):
        self.headless = headless
        self.max_concurrent = max_concurrent
        self.browser = None
        self.context = None
        self.results = []

    async def open_page(self, item):
        link = item["url"]
        limit = item.get("limit")

        page = await self.context.new_page()
        logger.debug("Page created")

        try:
            logger.info("Open url: %s", link)

            await page.goto("https://www.ozon.ru/", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            await human_scroll(page)

            await page.goto(link, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)

            await page.wait_for_selector(".tile-root", timeout=15000)

            results = []
            seen = set()
            stuck = 0
            prev_results_count = 0
            


            while True:
                if limit and len(results) >= limit:
                    break

                cards = await page.locator(
                    '[data-widget="tileGridDesktop"] .tile-root'
                ).all()

                if not cards:
                    break

                current_count = len(cards)

                logger.debug("cards=%s stuck=%s", current_count, stuck)

                for card in cards:
                    if limit and len(results) >= limit:
                        break

                    try:
                        data = await card.evaluate("""(card) => {
                            const linkEl = card.querySelector("a[target='_blank']");
                            const link = linkEl ? linkEl.getAttribute('href') : null;

                            const spans = Array.from(card.querySelectorAll("span"));

                            let price = "Нет цены";
                            let old_price = "Нет старой цены";

                            for (const el of spans) {
                                const text = el.innerText;
                                if (text.includes("₽")) {
                                    if (price === "Нет цены") price = text;
                                    else old_price = text;
                                }
                            }

                            const discountEl = spans.find(el => el.innerText.includes("%"));
                            const discount = discountEl ? discountEl.innerText : "Без скидки";

                            const ratingEl = spans.find(el => /^\\d\\.\\d/.test(el.innerText));
                            const rating = ratingEl ? ratingEl.innerText : "Нет рейтинга";

                            const reviewsEl = spans.find(el => el.innerText.includes("отзыв"));
                            const reviews = reviewsEl ? reviewsEl.innerText : "Нет отзывов";

                            return { link, price, old_price, discount, rating, reviews };
                        }""")
                    except Exception as e:
                        logger.debug("Card parse failed: %s", e)
                        continue

                    if not data or not data.get("link"):
                        continue

                    product_link = "https://www.ozon.ru" + data["link"]

                    if product_link in seen:
                        continue

                    seen.add(product_link)

                    results.append({
                        "link": product_link,
                        "price": data["price"],
                        "old_price": data["old_price"],
                        "discount": data["discount"],
                        "rating": data["rating"],
                        "reviews": data["reviews"]
                    })


                current_results_count = len(results)
                if current_results_count == prev_results_count:
                    stuck += 1
                else:
                    stuck = 0

                if stuck >= 10:
                    break

                prev_results_count = current_results_count


                await page.mouse.wheel(0, 3000)

                await asyncio.sleep(0.5)

                try:
                    await page.wait_for_function(
                        """(prev) => {
                            return document.querySelectorAll('[data-widget="tileGridDesktop"] .tile-root').length > prev;
                        }""",
                        current_count,
                        timeout=5000
                    )
                except:
                    pass

            return results

        finally:
            await page.close()


    async def scrape(self, links_settings):
        logger.info("Scrape started. links=%s", len(links_settings))
        self.results = []

        self.browser = await launch_async(headless=self.headless)
        self.context = await self.browser.new_context()

        sem = asyncio.Semaphore(self.max_concurrent)
        lock = asyncio.Lock()

        async def worker(item):
            async with sem:
                res = await self.open_page(item)

                async with lock:
                    self.results.extend(res)

        try:
            await asyncio.gather(*[worker(i) for i in links_settings])
        except Exception as e:
            logger.exception("Scrape failed: %s", e)
            raise
        finally:
            await self.browser.close()

        return self.results


    async def run(self, links_settings, save_formats=None):
        await self.scrape(links_settings)

        save_formats = save_formats or ["json", "csv", "xlsx"]

        if "json" in save_formats:
            save_json(self.results)

        if "csv" in save_formats:
            save_csv(self.results)

        if "xlsx" in save_formats:
            save_xlsx(self.results)

        return self.results