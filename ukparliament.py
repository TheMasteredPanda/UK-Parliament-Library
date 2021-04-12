from threading import Lock
from cachetools import TTLCache
from typing import Union
from structures.members import Party, PartyMember, LatestElectionResult, VotingEntry, ler_task, vh_task
from structures.bills import BillType, Bill, BillStage, Division
import bills as bills_utils
from bills import SearchBillsBuilder, SearchBillsSortOrder
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

class UKParliament:
    def __init__(self):
        self.parties: list[Party] = []
        self.bill_types: list[BillType] = []
        self.bill_stages: list[BillStage] = []
        self.old_member_cache = TTLCache(maxsize=90, ttl=600)
        self.old_member_cache_lock = Lock()
        self.bill_search_cache = TTLCache(maxsize=90, ttl=180)
        self.bill_search_cache_lock = Lock()
        self.division_cache = TTLCache(maxsize=90, ttl=600)
        self.division_cache_lock = Lock()
        self.voting_history_cache = TTLCache(maxsize=90, ttl=3600)
        self.voting_history_lock = Lock()

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

            ler_tasks = []

            for m in self.get_commons_members():
                ler_tasks.append(ler_task(m, session))

            
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



    async def get_voting_history(self, member: PartyMember) -> list[VotingEntry]:
        with self.voting_history_lock:
            cached_obj = self.voting_history_cache.get(member.get_id())
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            await asyncio.gather(vh_task(member, session, self.voting_history_cache, self.voting_history_lock))

        return await self.get_voting_history(member)

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
        with self.old_member_cache_lock:
            cached_obj = self.old_member_cache.get(member_id)
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{utils.URL_MEMBERS}/Members/{member_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't lazily load member under id {member_id}. Status Code: {resp.status}.")
                content = await resp.json()
                member = PartyMember(content)
                with self.old_member_cache_lock:
                    self.old_member_cache[member_id] = member
                return member

    def get_bill_stages(self):
        return self.bill_stages

    def get_bill_types(self):
        return self.bill_types

    async def search_bills(self, url: str) -> list[Bill]:
        with self.bill_search_cache_lock:
            cached_obj = self.bill_search_cache.get(url)
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch bills with url: {url}. Status Code: {resp.status}")

                content = await resp.json()
                bills = []

                extra_bill_information_tasks = []

                for item in content['items']:
                    bill = Bill(item)
                    extra_bill_information_tasks.append(bills_utils._meta_bill_task(bill, self, session))
                    bills.append(bill)
                await asyncio.gather(*extra_bill_information_tasks)
            
            with self.bill_search_cache_lock:
                self.bill_search_cache[url] = bills
            return bills

    async def get_commons_division(self, division_id: int):
        with self.division_cache_lock:
            cached_obj = self.division_cache.get(division_id)
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{utils.URL_COMMONS_VOTES}/division/{division_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch division {division_id}. Status Code: {resp.status}")
                content = await resp.json()

                division = Division(content)

                with self.division_cache_lock:
                    self.division_cache[division_id] = division
                return division
    
    async def get_lords_division(self, division_id: int):
        with self.division_cache_lock:
            cached_obj = self.division_cache.get(division_id)
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{utils.URL_LORDS_VOTES}/Divisions/{division_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch division {division_id}. Status Code: {resp.status}")
                content = await resp.json()
                division = Division(content)

                with self.division_cache_lock:
                    self.division_cache[division_id] = division
                return division


    async def search_for_lords_division(self, search_term: str):
        async with aiohttp.ClientSession() as session:
            formatted_search_term = "%20".join(search_term.split(' '))
            async with session.get(f"{utils.URL_LORDS_VOTES}/Divisions/searchTotalResults?SearchTerm={formatted_search_term}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch total search results for division search with query: '{search_term}. Status Code: {resp.status}")

                total_seach_results = await resp.json()
                division_items = await utils.load_data(f"{utils.URL_LORDS_VOTES}/Divisions/search?SearchTerm={formatted_search_term}", session, total_seach_results)

                divisions = []
                for item in division_items:
                    division = Division(item)
                    divisions.append(division)
                return divisions

    async def search_for_commons_divisions(self, search_term: str):
        async with aiohttp.ClientSession() as session:
            formatted_search_term = "%20".join(search_term.split(' '))
            async with session.get(f"{utils.URL_COMMONS_VOTES}/divisions.json/searchTotalResults?queryParameters.searchTerm={formatted_search_term}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch total search results for division search with query: '{search_term}'. Status Code: {resp.status}")
                
                total_search_results = await resp.json()
                division_items = await utils.load_data(f"{utils.URL_COMMONS_VOTES}/divisions.json/search?queryParameters.searchTerm={formatted_search_term}", session, total_search_results)
                
                divisions = []
                for item in division_items:
                    division = Division(item) #TODO cache it.
                    divisions.append(division)
                return divisions


parliament = UKParliament()
asyncio.run(parliament.load())
member = parliament.get_commons_members()[0]
print(f"Getting voting history of: {member.get_display_name()}/{member.get_id()}...")
print(len(asyncio.run(parliament.get_voting_history(member))))
