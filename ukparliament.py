from typing import Union
from structures.members import Party, PartyMember, LatestElectionResult
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
            async with session.get(f'{utils.URL_MEMBERS}/Parties/GetActive/Commons') as resp:
                if resp.status != 200:
                    raise Exception("Couldn't fetch active parties in the House of Commons")
                content = await resp.json()

                for item in content['items']:
                    self.parties.append(Party(item))

            async with session.get(f'{utils.URL_MEMBERS}/Parties/GetActive/Lords') as resp:
                if resp.status != 200:
                    raise Exception("Couldn't fetch active parties in the House of Lords")

                content = await resp.json()

                for item in content['items']:
                    party = self.get_party_by_id(item['value']['id'])
                    if party is None:
                        self.parties.append(Party(item))
                    else:
                        party._set_lords_party()
            json_party_members = await utils.load_data(f'{utils.URL_MEMBERS}/Members/Search?IsCurrentMember=true', session)


            ler_tasks = []

            async def ler_task(member_id: int, member: PartyMember):
                async with session.get(f'{utils.URL_MEMBERS}/Members/{member_id}/LatestElectionResult') as ler_resp:
                    if ler_resp.status != 200:
                        raise Exception(f"Couldn't fetch latest electio result for member {member_id}")

                    content = await ler_resp.json()
                    member._set_latest_election_result(LatestElectionResult(content))


            for json_member in json_party_members:
                member = PartyMember(json_member)
                party = self.get_party_by_id(member._get_party_id())
                
                if member.is_mp():
                    ler_tasks.append(ler_task(member.get_id(), member))

                if party is None:
                    print(f"Couldn't add member {member.get_titled_name()}/{member.get_id()} to party under apparent id {member._get_party_id()}")
                    continue
                party.add_member(member)

            await asyncio.gather(*ler_tasks)

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

    def get_commons_members(self) -> list[PartyMember]:
        members = []

        for party in self.parties:
            members.extend(party.get_mps())

        return members

    def get_lords_members(self):
        members = []

        for party in self.parties:
            members.extend(party.get_lords())

        return members

    async def search_bills_by_terms(self, query: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{utils.URL_BILLS}/Bills?query={"%20".join(query.split(" "))}') as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch list of bills. Status code: {resp.status}.")
                content = await resp.json()

                bills = []
                for item in content['items']:
                    bills.append(Bill(item))
                return bills
                    
    

parliament = UKParliament()
asyncio.run(parliament.load())
member = parliament.get_commons_members()[0]

