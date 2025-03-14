import asyncio
from typing import List, Tuple, Set
import trafilatura
from bs4 import BeautifulSoup, SoupStrainer
import aiohttp
from urllib.parse import urlunparse, urlparse, ParseResult
from dataclasses import dataclass
import json


TARGET = "https://www.wolfsburg.de/rathaus/buergerservice"
# TARGET = "https://quotes.toscrape.com"
OUTPUT_FILE = "output.txt"
MAX_DEPTH = 1
NUM_WORKERS = 8

output = {}


@dataclass
class Task:
    path: str
    depth: int


found = set()


def split_url(url: str) -> Tuple[str, str]:
    components = urlparse(url)

    return (components.netloc, components.path)


def get_links(page: str, netloc: str) -> List[str]:
    soup = BeautifulSoup(page, "html.parser")

    results = set()
    for el in soup.find_all("a"):
        url = el.get("href")
        link_netloc, path = split_url(url)

        if link_netloc and link_netloc != netloc:
            continue

        if path in found:
            continue

        if isinstance(path, bytes):
            path = ""

        results.add(path)

    return results


async def worker(session: aiohttp.ClientSession, netloc: str, queue: asyncio.Queue) -> Set[str]:
    while True:
        task = await queue.get()

        # Get page
        url = urlunparse(ParseResult(scheme="https", netloc=netloc, path=task.path, params="", query="", fragment=""))

        async with session.get(url) as page:
            data = await page.text()

        if task.depth < MAX_DEPTH:
            links = get_links(data, netloc)
            for link in links:
                await queue.put(Task(link, task.depth + 1))
                found.add(link)

        text = trafilatura.extract(data)

        output[task.path] = text

        with open("output.json", "w") as f:
            json.dump(output, f)

        print(f"Done {task.depth=} {queue.qsize()}")

        queue.task_done()

        if queue.qsize() == 0:
            break


async def main():
    netloc, path = split_url(TARGET)
    async with aiohttp.ClientSession() as session:
        queue = asyncio.Queue()

        queue.put_nowait(Task(path, 0))

        tasks = []
        for _ in range(NUM_WORKERS):
            task = asyncio.create_task(worker(session, netloc, queue))
            tasks.append(task)

        await queue.join()

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        with open("output.json", "w") as f:
            json.dump(output, f)

if __name__ == "__main__":
    asyncio.run(main())