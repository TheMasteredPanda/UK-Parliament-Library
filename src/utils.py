import math
import asyncio
import json
from enum import Enum
import aiohttp

URL_COMMONS_VOTES = 'https://commonsvotes-api.parliament.uk/data'
URL_LORDS_VOTES = 'https://lordsvotes-api.parliament.uk/data'
URL_MEMBERS = 'https://members-api.parliament.uk/api'
URL_BILLS = 'https://bills-api.parliament.uk/api'

class BetterEnum(Enum):
    @classmethod
    def from_name(cls, name: str):
        for option in cls:
            if option.name.lower() == name.lower():
                return option

async def load_data(url: str, session: aiohttp.ClientSession, total_search_results = -1):
    """
    Iterates through results that are pageinated and stiches all the results together.

    session: python modules Session instance for the UKParliament instance.

    """

    async with session.get(url) as resp:
        final_list = []
        is_division_url = url.startswith(URL_COMMONS_VOTES) or url.startswith(URL_LORDS_VOTES)

        async def task(t_url: str):
            async with session.get(t_url) as t_resp:
                if t_resp.status != 200:
                    raise Exception(f"Couldn't fetch data from {t_url}: Status Code: {t_resp.status}")
                t_content = await t_resp.json()
                final_list.extend(t_content['items'] if is_division_url is False else t_content)

        tasks = []
        if resp.status != 200:
            raise Exception(f"Couldn't fetch data from {url}: Status Code: {resp.status}")
        content = await resp.json()
        total_results = content['totalResults'] if 'totalResults' in content else content['totalItems'] if 'totalItems' in content else 0
        if total_search_results != -1: total_results = total_search_results
        pages = math.ceil(total_results / 20)
        element = '&'
        if '?' not in url:
            element = '?'

        for page in range(pages):
            skipSegment = f"{element}skip={page * 20}&take=20" if url.startswith(URL_COMMONS_VOTES) is False else f"{element}queryParameters.skip={page * 20}&queryParameters.take=20"
            tasks.append(task(f"{url}{skipSegment if page != 0 else ''}"))

        await asyncio.gather(*tasks)
        return final_list
