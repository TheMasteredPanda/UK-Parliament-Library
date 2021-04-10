from typing import Union
from structures.members import Party, PartyMember
import utils
import time
import asyncio
import json
import utils
import aiohttp

__author__ = 'TheMasteredPanda'
__status__ = 'Development'
__version__ = '1.0'

'''
---------------------------------------------------------
A Python Interface for the UK Parliament Rest API. 

The central point of contact is the UKParliament class,
each instance can index data from one election onwards,
until the date of the next election - this is to not
index unnecessary data. 
---------------------------------------------------------
'''

class UKParliament():
    def __init__(self):
        #self.member_functions = MemberFunctions()
        #self.constituencies_functions = ConstituenciesFunctions()
        self.parties: list[Party] = []
        pass

    async def load(self):
        async with aiohttp.ClientSession() as session: 
            async with session.get(f'{utils.APIURLS.MEMBERS}/Parties/GetActive/Commons') as resp:
                if resp.status != 200:
                    raise Exception("Couldn't fetch active parties in the House of Commons")
                content = await resp.json()

                for item in content['items']:
                    self.parties.append(Party(item))

            async with session.get(f'{utils.APIURLS.MEMBERS}/Parties/GetActive/Lords') as resp:
                if resp.status != 200:
                    raise Exception("Couldn't fetch active parties in the House of Lords")

                content = await resp.json()

                for item in content['items']:
                    party = self.get_party_by_id(item['value']['id'])
                    if party is None:
                        self.parties.append(Party(item))
                    else:
                        party._set_lords_party()
            json_party_members = await utils.load_data(f'{utils.APIURLS.MEMBERS}/api/Members/Search?IsCurrentMember=true', session)

            for json_member in json_party_members:
                member = PartyMember(json_member)
                self.get_party_by_id(member._get_party_id()).add_member(member)
                

    def get_party_by_name(self, name: str) -> Union[Party, None]:
        for party in self.parties:
            if party.get_name().lower() == name.lower():
                return party
        return None

    def get_party_by_id(self, party_id: int) -> Union[Party, None]:
        for party in self.parties:
            if party.get_party_id() == party_id:
                return party
        return None

    def get_commons_members(self):
        members = []

        for party in self.parties:
            members.extend(party.get_mps())

        return members

    def get_lords_members(self):
        members = []

        for party in self.parties:
            members.extend(party.get_lords())

        return members

parliament = UKParliament()
print(len(parliament.get_commons_members()))
