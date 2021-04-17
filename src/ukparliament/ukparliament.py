from threading import Lock
from aiohttp.client import ClientSession
from cachetools import TTLCache
from typing import Union
from .structures.members import Party, PartyMember, LatestElectionResult, VotingEntry, ler_task, vh_task
from .structures.bills import BillType, Bill, BillStage, CommonsDivision, LordsDivision
from . import bills
from .bills import _meta_bill_task
from . import utils
from .bills import division_task
import time
import asyncio
import json
import aiohttp

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
        self.division_search_commons_lock = Lock()
        self.division_search_commons_cache = TTLCache(maxsize=90, ttl=300)
        self.division_search_lords_lock = Lock()
        self.division_search_lords_cache = TTLCache(maxsize=90, ttl=300)
        self.bills_cache = TTLCache(maxsize=30, ttl=300)
        self.bills_cache_lock = Lock()

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

    async def get_bill(self, bill_id: int) -> Bill:
        with self.bills_cache_lock:
            cached_obj = self.bills_cache.get(bill_id)
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{utils.URL_BILLS}/Bills/{bill_id}") as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to fetch bill under id {bill_id}")
                content =  await resp.json()
                bill = Bill(content)
                await _meta_bill_task(bill, self, session)

                with self.bills_cache_lock:
                    self.bills_cache[bill_id] = bill
                return bill

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
                    extra_bill_information_tasks.append(_meta_bill_task(bill, self, session))
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
            async with session.get(f"{utils.URL_COMMONS_VOTES}/division/{division_id}.json") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch division {division_id}. Status Code: {resp.status}")
                content = await resp.json()

                division = CommonsDivision(content)
                await self._populate_commons_division(division)

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
                division = LordsDivision(content)
                await self._populate_lords_division(division)
                with self.division_cache_lock:
                    self.division_cache[division_id] = division
                return division


    async def search_for_lords_division(self, search_term: str) -> list[LordsDivision]:
        with self.division_search_lords_lock:
            cached_obj = self.division_search_lords_cache.get(search_term.lower())
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            formatted_search_term = "%20".join(search_term.split(' '))
            async with session.get(f"{utils.URL_LORDS_VOTES}/Divisions/searchTotalResults?SearchTerm={formatted_search_term}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch total search results for division search with query: '{search_term}. Status Code: {resp.status}")

                total_seach_results = await resp.json()
                division_items = await utils.load_data(f"{utils.URL_LORDS_VOTES}/Divisions/search?SearchTerm={formatted_search_term}", session, total_seach_results)

                divisions = []

                for item in division_items:
                    division = LordsDivision(item)
                    await self._populate_lords_division(division)
                    divisions.append(division)

                with self.division_search_lords_lock:
                    self.division_search_lords_cache[search_term.lower()] = divisions
                return divisions

    async def search_for_commons_divisions(self, search_term: str) -> list[CommonsDivision]:
        with self.division_search_commons_lock:
            cached_obj = self.division_search_commons_cache.get(search_term.lower())
            if cached_obj is not None:
                return cached_obj


        async with aiohttp.ClientSession() as session:
            formatted_search_term = "%20".join(search_term.split(' '))
            async with session.get(f"{utils.URL_COMMONS_VOTES}/divisions.json/searchTotalResults?queryParameters.searchTerm={formatted_search_term}") as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch total search results for division search with query: '{search_term}'. Status Code: {resp.status}")
                
                total_search_results = await resp.json()
                division_items = await utils.load_data(f"{utils.URL_COMMONS_VOTES}/divisions.json/search?queryParameters.searchTerm={formatted_search_term}", session, total_search_results)
                divisions = []
                for item in division_items:
                    division = CommonsDivision(item) 
                    await self._populate_commons_division(division)
                    divisions.append(division)

                with self.division_search_commons_lock:
                    self.division_search_commons_cache[search_term.lower()] = divisions
                return divisions


    async def _populate_lords_division(self, division: LordsDivision):
        aye_tellers = []
        a_teller_tasks = list(map(lambda teller: division_task(self, teller, aye_tellers), division._get_aye_teller_ids()))
        await asyncio.gather(*a_teller_tasks)
        division._set_aye_tellers(aye_tellers)
        no_tellers = []
        n_teller_tasks = list(map(lambda teller: division_task(self, teller, no_tellers), division._get_no_teller_ids()))
        await asyncio.gather(*n_teller_tasks)
        division._set_no_tellers(no_tellers)
        no_members = []
        n_members_tasks = list(map(lambda member_id: division_task(self, member_id, no_members), division._get_no_vote_member_ids()))
        await asyncio.gather(*n_members_tasks)
        division._set_no_members(no_members)

        aye_members = []
        a_members_tasks = list(map(lambda member_id: division_task(self, member_id, aye_members), division._get_aye_vote_member_ids()))
        await asyncio.gather(*a_members_tasks)
        division._set_aye_members(aye_members)


    async def _populate_commons_division(self, division: CommonsDivision):
        aye_tellers = []
        a_teller_tasks = list(map(lambda teller: division_task(self, teller, aye_tellers), division._get_aye_teller_ids()))
        await asyncio.gather(*a_teller_tasks)
        division._set_aye_members(aye_tellers)

        no_tellers = []
        n_teller_tasks = list(map(lambda teller: division_task(self, teller, no_tellers), division._get_no_teller_ids()))
        await asyncio.gather(*n_teller_tasks)
        
        aye_members = []
        aye_members_tasks = list(map(lambda member_id: division_task(self, member_id, aye_members), division._get_aye_member_ids()))
        await asyncio.gather(*aye_members_tasks)
        division._set_aye_members(aye_members)

        no_members = []
        no_members_tasks = list(map(lambda member_id: division_task(self, member_id, no_members), division._get_no_member_ids()))
        await asyncio.gather(*no_members_tasks)
        division._set_no_members(no_members)
