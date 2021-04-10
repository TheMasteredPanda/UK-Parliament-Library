import json
from enum import Enum
import aiohttp

class APIURLS(Enum):
    MEMBERS = 'https://members-api.parliament.uk/api/'

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

    async def iterate(url: str, results):
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Couldn't fetch data from url {url}: Status Code: {resp.status}")
            content = await resp.json()
            results.extend(content['items'])

            for link_id in content['links']:
                link = content['links'][link_id]
                if link['rel'] == 'page.next':
                    params = link.split('?')
                    url_params = url.split('&')
                    if len(url_params) == 1: 
                        url_params = url.split('?')
                        if len(url_params) == 1:
                            return iterate(f'{url}?{params[1]}', results)
                    modified_params = list(filter(lambda param: 'skip' not in param or 'take' not in param, url_params))
                    modified_params.append(params.split('&'))
                    return iterate(f'{url_params.pop(0)}?{"&".join(modified_params)}', results)
            return results

    
    return await iterate(url, [])
