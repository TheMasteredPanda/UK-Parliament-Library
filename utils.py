import json
import aiohttp
URL = 'http://eldaddp.azurewebsites.net'

async def load_data(url: str, session: aiohttp.ClientSession):
    """
    Iterates through results that are pageinated and stiches all the results together.

    session: python modules Session instance for the UKParliament instance.
    url: The URL of the first (page 0) page.
    """

    async def iterate(url: str, results: list):
        split_url = url.split('&')
        if len(split_url) == 1: split_url = url.split('?')
        page_size = list(filter(lambda k: '_pageSize=' in k, split_url))[0].split('=')[1]
        async with aiohttp.ClientSession().get(url) if session is None else session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Couldn't continue to iterate over pages of data as {url} responded with error code {resp.status}")
            content = await resp.json()
            if len(content['result']['items']) > 0: results.extend(content['result']['items'])

            if 'next' not in content['result']:
                return results
            else:
                if page_size == -1:
                    return await iterate(content['result']['next'], results)
                else:
                    return await iterate(f"{content['result']['next']}&_pageSize={page_size}", results)

    return await iterate(url, [])
