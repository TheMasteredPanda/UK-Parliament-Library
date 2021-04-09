import asyncio
from structures.elections import ElectionResult
from structures.members import PartyMember, Party
import aiohttp
import json
import utils

class MemberFunctions():
    def __init__(self):
        self.members = []

    '''
    - Use election results to determine the currently sitting members.
    '''
    async def _index(self, session: aiohttp.ClientSession, results: list[ElectionResult], c_functions):

        tasks = []
        async def _fetch_task(result):
            async with session.get(f'{utils.URL}/members.json?constituency={result._get_constituency_resource()}') as resp:
                if resp.status != 200: raise Exception(f"Couldn't fetch member by representing constituency. Status Code: {resp.status}")
                content = await resp.json()
                member = PartyMember.create(content['result']['items'][0])
                member._set_constituency(c_functions.get_constituency_by_id(result_item.get_constituency_id()))
                return member

        for result_item in results:
            tasks.append(_fetch_task(result_item))

        self.members.extend(await asyncio.gather(*tasks))
        
    def get_members(self):
        return self.members
