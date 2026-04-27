import asyncio
import random


async def human_scroll(page):
    for _ in range(random.randint(3, 8)):
        await page.mouse.wheel(0, random.randint(300, 900))
        await asyncio.sleep(random.uniform(0.3, 0.8))