import math
import asyncio
import json
from enum import Enum
import aiohttp

URL_MEMBERS = 'https://members-api.parliament.uk/api'
URL_BILLS = 'https://bills-api.parliament.uk/api'

class BetterEnum(Enum):
    @classmethod
    def from_name(cls, name: str):
        for option in cls:
            if option.name.lower() == name.lower():
                return option

async def load_data(url: str, session: aiohttp.ClientSession):
    """
    Iterates through results that are pageinated and stiches all the results together.

    session: python modules Session instance for the UKParliament instance.

    """


    async with session.get(url) as resp:
        final_list = []

        async def task(t_url: str):
            async with session.get(t_url) as t_resp:
                if t_resp.status != 200:
                    raise Exception(f"Couldn't fetch data from {t_url}: Status Code: {t_resp.status}")
                t_content = await t_resp.json()
                final_list.extend(t_content['items'])

        tasks = []
        if resp.status != 200:
            raise Exception(f"Couldn't fetch data from {url}: Status Code: {resp.status}")
        content = await resp.json()
        totalResults = content['totalResults']
        pages = math.ceil(totalResults / 20)

        for page in range(pages):
            tasks.append(task(f"{url}&skip={page * 20}"))

        await asyncio.gather(*tasks)
        return final_list
