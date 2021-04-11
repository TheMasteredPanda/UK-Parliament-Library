from typing import Union
from structures.members import Party, PartyMember, LatestElectionResult
from structures.bills import BillType, Bill, BillStage
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
        self.parties: list[Party] = []
        self.bill_types: list[BillType] = []
        self.bill_stages: list[BillStage] = []

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
            for json_member in json_party_members:
                member = PartyMember(json_member)
                party = self.get_party_by_id(member._get_party_id())

                if party is None:
                    print(f"Couldn't add member {member.get_titled_name()}/{member.get_id()} to party under apparent id {member._get_party_id()}")
                    continue
                party.add_member(member)

            async def ler_task(ler_member: PartyMember):
                async with session.get(f'{utils.URL_MEMBERS}/Members/{ler_member.get_id()}/LatestElectionResult') as ler_resp:
                    if ler_resp.status != 200:
                        return
                    
                    content = await ler_resp.json()
                    ler_member._set_latest_election_result(LatestElectionResult(content))


            ler_tasks = []

            for m in self.get_commons_members():
                ler_tasks.append(ler_task(m))


            
            await asyncio.gather(*ler_tasks)

            async with session.get(f'{utils.URL_BILLS}/BillTypes') as bt_resp:
                if bt_resp.status != 200:
                    raise Exception(f"Couldn't fetch bill types. Status Code: {bt_resp.status}")

                content = await bt_resp.json()

                for item in content['items']:
                    self.bill_types.append(BillType(item))
                
            json_bill_stages = await utils.load_data(f'{utils.URL_BILLS}/Stages', session)

            for json_bill_stage in json_bill_stages:
                self.bill_stages.append(BillStage(json_bill_stage))


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

    def get_lords_members(self) -> list[PartyMember]:
        members = []

        for party in self.parties:
            members.extend(party.get_lords())

        return members

    def get_member_by_id(self, member_id: int) -> Union[PartyMember, None]:
        for member in self.get_commons_members():
            if member.get_id() == member_id:
                return member
        for member in self.get_lords_members():
            if member.get_id() == member_id:
                return member
        return None

    def get_member_by_name(self, member_name: str) -> Union[PartyMember, None]:
        for member in self.get_commons_members():
            if member_name is member.get_display_name():
                return member
        return None

    #Cheap Workaround to using a cache, something I'll implement later
    async def _lazy_load_member(self, member_id: int) -> PartyMember:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{utils.URL_MEMBERS}/Members/{member_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't lazily load member under id {member_id}. Status Code: {resp.status}.")
                content = await resp.json()
                return PartyMember(content)


    async def search_bills_by_terms(self, query: str) -> list[Bill]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{utils.URL_BILLS}/Bills?SearchTerm={"%20".join(query.split(" "))}&SortOrder=DateUpdatedDescending') as resp:
                print(resp.url)
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch bills with query: {query}. Status Code: {resp.status}")

                async def search_bill_task(bill: Bill):
                    async with session.get(f"{utils.URL_BILLS}/Bills/{bill.get_bill_id()}") as bill_resp:
                        if bill_resp.status != 200:
                            raise Exception(f"Couldn't fetch information for from url: '{bill_resp.url}'/{bill.get_title()}. Status Code: {bill_resp.status}")
                        bill_content = await bill_resp.json()
                        sponsors = bill_content['value']['sponsors']

                        pm_sponsors = []
                        bill._set_long_title(bill_content['value']['longTitle'])
                        if sponsors is not None and len(sponsors) > 0:
                            for json_sponsor in sponsors:
                                member = self.get_member_by_id(json_sponsor['memberId'])
                                if member is None:
                                    member = await self._lazy_load_member(json_sponsor['memberId'])

                                    if member is None:
                                        raise Exception(f"Couldn't find sponsor party member instance of sponsor {json_sponsor['name']}/{json_sponsor['memberId']}")
                                pm_sponsors.append(member)
                            bill._set_sponsors(pm_sponsors)

                content = await resp.json()
                bills = []

                extra_bill_information_tasks = []

                for item in content['items']:
                    bill = Bill(item)
                    extra_bill_information_tasks.append(search_bill_task(bill))
                    bills.append(bill)
                await asyncio.gather(*extra_bill_information_tasks)
            
            return bills

parliament = UKParliament()
asyncio.run(parliament.load())
member = parliament.get_commons_members()[0]
bills = asyncio.run(parliament.search_bills_by_terms('European Withdrawal'))
print(bills[0].get_sponsors()[0].get_display_name())

