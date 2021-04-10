import json
from enum import Enum
import aiohttp

URL_MEMBERS = 'https://members-api.parliament.uk/api'

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
            
            for link in content['links']:
                if link['rel'] == 'page.next':
                    params = link['href'].split('?')
                    url_params = url.split('&')
                    if len(url_params) == 1: 
                        url_params = url.split('?')
                        if len(url_params) == 1:
                            return await iterate(f'{url}?{params[1]}', results)
                    modified_params = list(filter(lambda param: 'skip' not in param and 'take' not in param, url_params))
                    modified_params.extend(params[1].split('&'))
                    new_url = f"{modified_params.pop(0)}{'?' if '?' not in url_params[0] else '&'}{'&'.join(modified_params)}"
                    if new_url == url: return results
                    return await iterate(new_url, results)
            return results

    
    return await iterate(url, [])
