
import asyncio
from tools.searchweb import search_web_serp
from dotenv import load_dotenv
import os

load_dotenv()

async def test_serp_tool():
    results = await search_web_serp("nyimbo", max_results=5)
    print(results)

if __name__ == "__main__":
    asyncio.run(test_serp_tool())