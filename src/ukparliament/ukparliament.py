import asyncio
from datetime import datetime
from threading import Lock
from typing import Union

import aiohttp
import bs4
from aiohttp.client import ClientSession
from cachetools import TTLCache

from . import utils
from .bills import _meta_bill_task, division_task
from .bills_tracker import (BillsStorage, BillsTracker, PublicationsTracker,
                            dual_event_loop)
from .divisions_tracker import DivisionStorage, DivisionsTracker
from .members import er_task, vh_task
from .structures.bills import (Bill, BillStage, BillType, CommonsDivision,
                               LordsDivision)
from .structures.members import (ElectionResult, Party, PartyMember,
                                 PartyMemberBiography, VotingEntry)

"""
---------------------------------------------------------
A Python Interface for the UK Parliament Rest API.

The central point of contact is the UKParliament class,
each instance can index data from one election onwards,
until the date of the next election - this is to not
index unnecessary data.
---------------------------------------------------------
"""


class UKParliament:
    def __init__(self, session: ClientSession):
        self.session = session
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
        self.election_results_cache = TTLCache(maxsize=90, ttl=300)
        self.election_results_lock = Lock()
        self.bills_tracker = None
        self.divisions_tracker = None
        self.publications_tracker = None
        print(f"BS4 Version: {bs4.__version__}")

    def start_publications_tracker(self, tracker: BillsTracker):
        """
        Creates a tracker to track publications related to a bill.

        Parameters
        ----------
        tracker: :class:`BillsTracker`
            The tracker for bills.

        """
        self.publications_tracker = PublicationsTracker(tracker)

    def get_publications_tracker(self):
        """
        Returns a publications tracker instance.
        """
        return self.publications_tracker

    def start_bills_tracker(self, storage: BillsStorage):
        """
        Creates a tracker to track bills being passed through Parliament.

        Parameters
        ----------
        storage: :class:`BillsStorage`
            The inferface used to store data relevant to the tracker.
        """
        self.bills_tracker = BillsTracker(self, storage, self.session)

    async def load_bills_tracker(self):
        """
        Loads the bills tracker and publications tracker if a PublicationsTracker instance
        is present, otherwise just the BillsTracker instance.
        """
        if self.bills_tracker is None:
            return
        if self.publications_tracker is None:
            await self.bills_tracker.start_event_loop()
        else:
            await dual_event_loop(self.bills_tracker, self.publications_tracker)

    def get_bills_tracker(self) -> Union[BillsTracker, None]:
        """
        Returns the bills tracker instance.
        """
        return self.bills_tracker

    def start_divisions_tracker(self, storage: DivisionStorage):
        """
        Creates a tracker to track divisions, both from the House of Commons
        and the House of Lords.

        Parameters
        ----------
        storage: :class:`DivisionStorage`
            The interface used to store data relevant to the tracker.
        """
        self.divisions_tracker = DivisionsTracker(self, storage)

    async def load_divisions_tracker(self):
        """
        Loads the DivisionTracker instance, starts the event loop.
        """
        if self.divisions_tracker is None:
            return
        await self.divisions_tracker.start_event_loop()

    def get_divisions_tracker(self) -> Union[DivisionsTracker, None]:
        """
        Returns the DivisionTracker instance.
        """
        return self.divisions_tracker

    async def load(self):
        """
        Loads the UKParliament instance. Indexed parties, party members (MPs and Lords),
        Bill types and Bill stages.
        """
        async with self.session.get(
            f"{utils.URL_MEMBERS}/Parties/GetActive/Commons"
        ) as resp:
            if resp.status != 200:
                print(resp.url)
                raise Exception("Couldn't fetch active parties in the House of Commons")
            content = await resp.json()

            for item in content["items"]:
                self.parties.append(Party(item))

        async with self.session.get(
            f"{utils.URL_MEMBERS}/Parties/GetActive/Lords"
        ) as resp:
            if resp.status != 200:
                raise Exception("Couldn't fetch active parties in the House of Lords")

            content = await resp.json()

            for item in content["items"]:
                party = self.get_party_by_id(item["value"]["id"])
                if party is None:
                    self.parties.append(Party(item))
                else:
                    party.set_lords_party()

        json_party_members = await utils.load_data(
            f"{utils.URL_MEMBERS}/Members/Search?IsCurrentMember=true", self.session
        )
        for json_member in json_party_members:
            member = PartyMember(json_member)
            party = self.get_party_by_id(member.get_party_id())

            if party is None:
                print(
                    f"Couldn't add member {member.get_titled_name()}/{member.get_id()} to party"
                    f" under apparent id {member.get_party_id()}"
                )
                continue

            party.add_member(member)

        async with self.session.get(f"{utils.URL_BILLS}/BillTypes") as bt_resp:
            if bt_resp.status != 200:
                raise Exception(
                    f"Couldn't fetch bill types. Status Code: {bt_resp.status}"
                )

            content = await bt_resp.json()

            for item in content["items"]:
                self.bill_types.append(BillType(item))

        json_bill_stages = await utils.load_data(
            f"{utils.URL_BILLS}/Stages", self.session
        )

        for json_bill_stage in json_bill_stages:
            bill_stage = BillStage(json_bill_stage)
            self.bill_stages.append(bill_stage)

    async def get_biography(self, member: PartyMember) -> PartyMemberBiography:
        """
        Fetches the biography of a party member (Lord or Member of Parliament).

        Parameters
        ----------
        member: :class:`PartyMember`
            A Member of Parliament or Lord.

        Returns
        -------
        Returns a :class:`PartyMemberBiography` instance, containing information about a
        members biography fetches from the UKParliament REST API.
        """
        async with self.session.get(
            f"https://members-api.parliament.uk/api/Members/{member.get_id()}/Biography"
        ) as bio_resp:
            if bio_resp.status != 200:
                raise Exception(
                    f"Couldn't load member bio of {member.get_id()}/{member.get_listed_name()}."
                    f" Status Code: {bio_resp.status}"
                )
            bio_content = await bio_resp.json()
            return PartyMemberBiography(bio_content)

    async def get_election_results(self, member: PartyMember) -> list[ElectionResult]:
        """
        Fetches the election results of a constituency via the representing member.

        Parameters
        ----------
        member: :class:`PartyMember`
            The Member of Parliament representing a constituency.

        Returns
        -------
        A list of :class:`ElectionResult` instances, containg the election result history of
        that constituency.
        """
        with self.election_results_lock:
            cached_obj = self.election_results_cache.get(
                member._get_membership_from_id()
            )
            if cached_obj is not None:
                return cached_obj

        election_result = await asyncio.gather(er_task(member, self.session))
        elections = election_result[0]

        with self.election_results_lock:
            self.election_results_cache[member._get_membership_from_id()] = elections
        return elections  # type: ignore

    async def get_voting_history(self, member: PartyMember) -> list[VotingEntry]:
        """
        Fetches the voting history of a party member.

        Parameters
        ----------
        member: :class:`PartyMember`
            The Member of Parliament or Lord.

        Returns
        -------
        A list of :class:`VotingEntry` instances.
        """
        with self.voting_history_lock:
            cached_obj = self.voting_history_cache.get(member.get_id())
            if cached_obj is not None:
                return cached_obj

        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                vh_task(
                    member, session, self.voting_history_cache, self.voting_history_lock
                )
            )

        return await self.get_voting_history(member)

    def get_party_by_name(self, name: str) -> Union[Party, None]:
        """
        Fetches a :class:`Party` instance via the party name.

        Parameters
        ----------
        name: :class:`str`
            Name of the Party to fetch.

        Returns
        -------
        Returns an instance of a :class:`Party`
        """
        for party in self.parties:
            if party.get_name().lower() == name.lower():
                return party
        return None

    def get_party_by_id(self, party_id: int) -> Union[Party, None]:
        """
        Fetches a :class:`Party` instance via the party id.

        Parameters
        ----------
        party_id:`int`
            The id of a party.

        Returns
        -------
        Returns an instance of a :class:`Party`
        """
        for party in self.parties:
            if party.get_party_id() == party_id:
                return party
        return None

    def get_commons_members(self) -> list[PartyMember]:
        """
        Returns a list of :class:`PartyMember` instances,
        all of which containing information on Members of Parliament.
        """
        members = []

        for party in self.parties:
            members.extend(party.get_mps())

        return members

    def get_lords_members(self) -> list[PartyMember]:
        """
        Returns a list of :class:`PartyMember` instances,
        all of which containing information on Aristocrats (Lords)
        """
        members = []

        for party in self.parties:
            members.extend(party.get_lords())

        return members

    def get_member_by_id(self, member_id: int) -> Union[PartyMember, None]:
        """
        Fetches a :class:`PartyMember` via the member id.

        Parameters
        ----------
        member_id: :class:`int`
            The id of a :class:`PartyMember`

        Returns
        -------
        A :class:`PartyMember` instance.
        """
        for member in self.get_commons_members():
            if member.get_id() == member_id:
                return member
        for member in self.get_lords_members():
            if member.get_id() == member_id:
                return member
        return None

    def get_member_by_name(self, member_name: str) -> Union[PartyMember, None]:
        """
        Fetches a :class:`PartyMember` via the member's name.

        Parameters
        ----------
        member_name: :class:`str`
            The name of a :class:`PartyMember`

        Returns
        -------
        A :class:`PartyMember` instance.
        """
        for member in self.get_commons_members():
            if member_name.lower() is member.get_display_name().lower():
                return member
        return None

    # Cheap Workaround to using a cache, something I'll implement later
    async def lazy_load_member(self, member_id: int) -> PartyMember:
        """
        Fetches a party member lazily. Meaning that the party member data is fetched and
        a :class:`PartyMember` is instantiated rather than the data being indexed when
        within the :func:`load` function.

        Parameters
        ----------
        member_id:`int`
            The id of a :class:`PartyMember`

        Returns
        -------
        A :class:`PartyMember` instance.
        """
        with self.old_member_cache_lock:
            cached_obj = self.old_member_cache.get(member_id)
            if cached_obj is not None:
                return cached_obj

        async with self.session.get(f"{utils.URL_MEMBERS}/Members/{member_id}") as resp:
            if resp.status != 200:
                raise Exception(
                    f"Couldn't lazily load member under id {member_id}. Status Code: {resp.status}."
                )
            content = await resp.json()
            member = PartyMember(content)
            return member

    def get_bill_stages(self) -> list[BillStage]:
        """
        Returns a list of :class:`BillStage` instances.
        """
        return self.bill_stages

    def get_bill_types(self) -> list[BillType]:
        """
        Returns a list of :class:`BillType` instances.
        """
        return self.bill_types

    async def get_bill(self, bill_id: int) -> Bill:
        """
        Fetches a :class:`Bill` via the bill's id.

        Parameters
        ----------
        bill_id: :class:`int`
            The id of a :class:`Bill`

        Returns
        -------
        A :class:`Bill` instance.
        """
        with self.bills_cache_lock:
            cached_obj = self.bills_cache.get(bill_id)
            if cached_obj is not None:
                return cached_obj

        async with self.session.get(f"{utils.URL_BILLS}/Bills/{bill_id}") as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch bill under id {bill_id}")
            content = await resp.json()
            bill = Bill(content)
            await _meta_bill_task(bill, self, self.session)

            with self.bills_cache_lock:
                self.bills_cache[bill_id] = bill
            return bill

    async def search_bills(self, url: str) -> list[Bill]:
        """
        Fetches a list of bills returned from the url, usually built from :class:`SearchBillsBuilder`

        Parameters
        ----------
        url: :class:`str`
            The url of a bill search.

        Returns
        -------
        A list of :class:`Bill` instances.
        """
        with self.bill_search_cache_lock:
            cached_obj = self.bill_search_cache.get(url)
            if cached_obj is not None:
                return cached_obj

        async with self.session.get(url) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Couldn't fetch bills with url: {url}. Status Code: {resp.status}"
                )

            content = await resp.json()
            bills = []

            extra_bill_information_tasks = []

            for item in content["items"]:
                bill = Bill(item)
                extra_bill_information_tasks.append(
                    _meta_bill_task(bill, self, self.session)
                )
                bills.append(bill)
            await asyncio.gather(*extra_bill_information_tasks)

            with self.bill_search_cache_lock:
                self.bill_search_cache[url] = bills
            return bills

    async def get_commons_division(self, division_id: int) -> CommonsDivision:
        """
        Fetches a :class:`CommonsDivision` via the division id.

        Parameters
        ----------
        division_id: :class:`int`
            The id of a division.

        Returns
        -------
        Returns a :class:`CommonsDivision` instance.
        """
        with self.division_cache_lock:
            cached_obj = self.division_cache.get(division_id)
            if cached_obj is not None:
                return cached_obj

        async with self.session.get(
            f"{utils.URL_COMMONS_VOTES}/division/{division_id}.json"
        ) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Couldn't fetch division {division_id}. Status Code: {resp.status}"
                )
            content = await resp.json()

            division = CommonsDivision(content)
            await self._populate_commons_division(division)

            with self.division_cache_lock:
                self.division_cache[division_id] = division
            return division

    async def get_lords_division(self, division_id: int):
        """
        Fetches a :class:`LordsDivision` via the division id.

        Parameters
        ----------
        division_id: :class:`int`
            The id of a division.

        Returns
        -------
        Returns a :class:`LordsDivision` instance.
        """
        with self.division_cache_lock:
            cached_obj = self.division_cache.get(division_id)
            if cached_obj is not None:
                return cached_obj

        async with self.session.get(
            f"{utils.URL_LORDS_VOTES}/Divisions/{division_id}"
        ) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Couldn't fetch division {division_id}. Status Code: {resp.status}"
                )
            content = await resp.json()
            division = LordsDivision(content)
            await self._populate_lords_division(division)
            with self.division_cache_lock:
                self.division_cache[division_id] = division
            return division

    async def search_for_lords_divisions(
        self, search_term: str = "", result_limit: int = -1
    ) -> list[LordsDivision]:
        """
        Fetches a list of :class:`LordsDivision` instances via a string (search term)

        Parameters
        ----------
        search_term: :class:`str`
            The search term to search for in lords divisions.
        result_limit: :class:`int`
            The limit of divsions to return.

        Returns
        -------
        Returns a list of :class:`LordsDivision` instances.
        """
        if search_term != "":
            with self.division_search_lords_lock:
                cached_obj = self.division_search_lords_cache.get(search_term.lower())
                if cached_obj is not None:
                    return cached_obj

        async def get_total_results(search_term: str):
            async with self.session.get(
                (
                    f"{utils.URL_LORDS_VOTES}/Divisions/searchTotalResults"
                    f"?SearchTerm={formatted_search_term}"
                )
            ) as resp:
                if resp.status != 200:
                    raise Exception(
                        "Couldn't fetch total search results for division search with query: "
                        f"{search_term}. Status Code: {resp.status}"
                    )
                return await resp.json()

        formatted_search_term = "%20".join(search_term.split(" "))
        total_search_results = (
            await get_total_results(formatted_search_term)
            if result_limit == -1
            else result_limit
        )

        division_items = await utils.load_data(
            f"{utils.URL_LORDS_VOTES}/Divisions/search"
            + (f"?SearchTerm={formatted_search_term}" if search_term != "" else ""),
            self.session,
            total_search_results,
        )

        divisions = []

        for item in division_items:
            division = LordsDivision(item)
            await self._populate_lords_division(division)
            divisions.append(division)

        if search_term != "":
            with self.division_search_lords_lock:
                self.division_search_lords_cache[search_term.lower()] = divisions

        return divisions

    async def search_for_commons_divisions(
        self, search_term: str = "", result_limit: int = -1
    ) -> list[CommonsDivision]:
        """
        Fetches a list of :class:`CommonsDivision` isntances via a string (search term)

        Parameters
        ----------
        search_term: :class:`str`
            The search term to search for in the commons divisions.
        result_limit: :class:`int`
            The limit of commons divisions to return.

        Returns
        -------
        Returns a list of :class:`CommonsDivision` instances.
        """
        if search_term != "":
            with self.division_search_commons_lock:
                cached_obj = self.division_search_commons_cache.get(search_term.lower())
                if cached_obj is not None:
                    return cached_obj

        async def get_total_results(search_term: str):
            async with self.session.get(
                f"{utils.URL_COMMONS_VOTES}/divisions.json/searchTotalResults"
                f"?queryParameters.searchTerm={formatted_search_term}"
            ) as resp:
                if resp.status != 200:
                    raise Exception(
                        "Couldn't fetch total search results for division search with query:"
                        f" '{search_term}. Status Code: {resp.status}"
                    )

                total_search_results = await resp.json()
                return total_search_results

        formatted_search_term = "%20".join(search_term.split(" "))
        total_search_results = (
            await get_total_results(formatted_search_term)
            if result_limit == -1
            else result_limit
        )

        division_items = await utils.load_data(
            f"{utils.URL_COMMONS_VOTES}/divisions.json/search"
            + (
                f"?queryParameters.searchTerm={formatted_search_term}"
                if search_term != ""
                else ""
            ),
            self.session,
            total_search_results,
        )
        divisions = []
        for item in division_items:
            division = CommonsDivision(item)
            await self._populate_commons_division(division)
            divisions.append(division)

        if search_term != "":
            with self.division_search_commons_lock:
                self.division_search_commons_cache[search_term.lower()] = divisions

        return divisions

    def get_parties(self) -> list[Party]:
        """
        Fetches a list of :class:`Party` instances.
        """
        return self.parties

    async def _populate_lords_division(self, division: LordsDivision):
        """
        Populates a :class:`LordsDivision` with references to data already
        indexed, primarily :class:`PartyMember` instances.

        Parameters
        ----------
        division: :class:`LordsDivision`
            The division instance to populate.
        """
        aye_tellers = []
        a_teller_tasks = list(
            map(
                lambda teller: division_task(self, teller, aye_tellers),
                division.get_aye_teller_ids(),
            )
        )
        await asyncio.gather(*a_teller_tasks)
        division.set_aye_tellers(aye_tellers)
        no_tellers = []
        n_teller_tasks = list(
            map(
                lambda teller: division_task(self, teller, no_tellers),
                division.get_no_teller_ids(),
            )
        )
        await asyncio.gather(*n_teller_tasks)
        division.set_no_tellers(no_tellers)
        no_members = []
        n_members_tasks = list(
            map(
                lambda member_id: division_task(self, member_id, no_members),
                division.get_no_vote_member_ids(),
            )
        )
        await asyncio.gather(*n_members_tasks)
        division.set_no_members(no_members)

        aye_members = []
        a_members_tasks = list(
            map(
                lambda member_id: division_task(self, member_id, aye_members),
                division.get_aye_vote_member_ids(),
            )
        )
        await asyncio.gather(*a_members_tasks)
        division.set_aye_members(aye_members)

    async def _populate_commons_division(self, division: CommonsDivision):
        """
        Populates a :class:`CommonsDivision` with references to data already
        indexed, primarily :class:`PartyMember` instances.

        Parameters
        ----------
        division: :class:`CommonsDivision`
            The division instance to populate.
        """
        aye_tellers = []
        a_teller_tasks = list(
            map(
                lambda teller: division_task(self, teller, aye_tellers),
                division.get_aye_teller_ids(),
            )
        )
        await asyncio.gather(*a_teller_tasks)
        division.set_aye_members(aye_tellers)

        no_tellers = []
        n_teller_tasks = list(
            map(
                lambda teller: division_task(self, teller, no_tellers),
                division.get_no_teller_ids(),
            )
        )
        await asyncio.gather(*n_teller_tasks)

        aye_members = []
        aye_members_tasks = list(
            map(
                lambda member_id: division_task(self, member_id, aye_members),
                division.get_aye_member_ids(),
            )
        )
        await asyncio.gather(*aye_members_tasks)
        division.set_aye_members(aye_members)

        no_members = []
        no_members_tasks = list(
            map(
                lambda member_id: division_task(self, member_id, no_members),
                division.get_no_member_ids(),
            )
        )
        await asyncio.gather(*no_members_tasks)
        division.set_no_members(no_members)
