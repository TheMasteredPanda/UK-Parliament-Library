from threading import Lock
from cachetools import TTLCache
from enum import Enum
import datetime
import aiohttp
import dateparser
from typing import Union
import utils
from utils import BetterEnum, load_data


class GoverningCapacity(BetterEnum):
    SINGLE_PARRTY_GOVERNMENT = 0
    COALITION_PARTY_GOVERNMENT = 1
    CAS_OPPOSITION_PARTY = 2
    OFFICIAL_OPPOSITION = 3

    @classmethod
    def from_value(cls, value: int):
        for option in cls:
            if option.value == value:
                return value
        raise Exception(f'{value} was not associated with any of the enums')

class VotingEntry:
    def __init__(self, json_object):
        value_object = json_object['value']
        self.house = value_object['house']
        self.voting_id = value_object['id']
        self.vote = value_object['inAffirmativeLobby']
        self.teller = value_object['actedAsTeller']
        self.division_url = json_object['links'][0]['href']

    def get_house(self):
        return self.house

    def get_id(self):
        return self.voting_id

    def voted_aye(self):
        return self.voted_aye

    def was_teller(self):
        return self.teller

    def get_division_id(self):
        return self.division_url.split('/')[-1].replace('.json','')

class LatestElectionResult:
    def __init__(self, json_object):
        value_object = json_object['value']
        self.result = value_object['result']
        self.notional = value_object['isNotional']
        self.electorate = value_object['electorate']
        self.turnout = value_object['turnout']
        self.majority = value_object['majority']
        self.candidates = []

        for candidate_object in value_object['candidates']:
            candidate_name = candidate_object['name']
            candidate_party_id = candidate_object['party']['id']
            vote_share_change = candidate_object['resultChange']
            candidate_order = candidate_object['rankOrder']
            votes_received = candidate_object['votes']
            vote_share = candidate_object['voteShare']

    def get_result(self) -> str:
        return self.result

    def get_notional(self) -> bool:
        return self.notional

    def get_electorate_size(self) -> int:
        return self.electorate

    def get_turnout(self) -> int:
        return self.turnout

    def get_majority(self) -> int:
        return self.majority

    def get_candidates(self) -> list[dict]:
        return self.candidates
        
class PartyMember:
    def __init__(self, json_object):
        value_object = json_object['value']
        self.member_id = value_object['id']
        self.titled_name = value_object['nameFullTitle']
        self.addressed_name = value_object['nameAddressAs']
        self.displayed_name = value_object['nameDisplayAs']
        self.listed_name = value_object['nameListAs']
        self._party_id = value_object['latestParty']['id']
        self.gender = value_object['gender']
        self.started = dateparser.parse(value_object['latestHouseMembership']['membershipStartDate'])
        self.thumbnail = value_object['thumbnailUrl']
        self._house_id = value_object['latestHouseMembership']['house']
        self.membership_from = value_object['latestHouseMembership']['membershipFrom']
        self._membership_id = value_object['latestHouseMembership']['membershipFromId']
        self.latest_election_result = None

    def _set_latest_election_result(self, result: LatestElectionResult):
        self.latest_election_result = result

    def _get_membership_from_id(self) -> int:
        return self._membership_id

    def get_latest_election_result(self) -> Union[LatestElectionResult, None]:
        return self.latest_election_result

    def get_membership_from(self) -> str:
        return self.membership_from #If it is a Lord then this will show the Lords membership status (life, hereditary, &c). If this is a commons member this will show the constitueny the member is representing.

    def is_mp(self) -> bool:
        return self._house_id != 2

    def _get_house(self) -> int:
        return self._house_id

    def get_id(self) -> int:
        return self.member_id

    def get_titled_name(self) -> str:
        return self.titled_name

    def get_display_name(self) -> str:
        return self.displayed_name
    
    def get_addressed_name(self) -> str:
        return self.addressed_name

    def get_listed_name(self) -> str:
        return self.listed_name

    def _get_party_id(self) -> int:
        return self._party_id

    def get_gender(self) -> str:
        return self.gender

    def get_started_date(self) -> Union[datetime.datetime, None]:
        return self.started

class Party:
    def __init__(self, json_object):
        value_object = json_object['value']
        self.party_id = value_object['id']
        self.name  = value_object['name']
        self.abbreviation = value_object['name']
        self.primary_colour = value_object['backgroundColour']
        self.secondary_colour = value_object['foregroundColour']
        self.lords_govt_party = value_object['isLordsMainParty']
        self.lords_party = self.lords_govt_party
        self.lords_spiritual_party = value_object['isLordsSpiritualParty']
        self.governing = value_object['governmentType'] is not None
        self.governing_capacity = GoverningCapacity.from_value(value_object['governmentType']) if json_object['value']['governmentType'] is not None else None
        self.independent_group = value_object['isIndependentParty']
        self.hoc_members = []
        self.hol_members = []

    def add_member(self, member: PartyMember):
        if member._get_house() == 2:
            self.hol_members.append(member)
        else:
            self.hoc_members.append(member)
    
    def _set_lords_party(self, lords_party: bool = True):
        self.lords_party = lords_party

    def get_name(self) -> str:
        return self.name

    def get_party_id(self) -> int:
        return self.party_id

    def get_all_members(self) -> list[PartyMember]:
        members = self.hoc_members.copy()
        members.extend(self.hol_members.copy())
        return members

    def get_mps(self) -> list[PartyMember]:
        return self.hoc_members

    def get_lords(self) -> list[PartyMember]:
        return self.hol_members

    def find_member_by_name(self, name: str) -> Union[PartyMember, None]:
        for member in self.get_all_members():
            if name in member.get_display_name() or name in member.get_titled_name() or name in member.get_addressed_name():
                return member
        return None

    def find_member_by_constituency_postcode(self, postcode: str) -> Union[PartyMember, None]:
        pass

async def ler_task(ler_member: PartyMember, session: aiohttp.ClientSession):
    async with session.get(f'{utils.URL_MEMBERS}/Members/{ler_member.get_id()}/LatestElectionResult') as ler_resp:
        if ler_resp.status != 200:
            return
        
        content = await ler_resp.json()
        ler_member._set_latest_election_result(LatestElectionResult(content))

async def vh_task(vi_member: PartyMember, session: aiohttp.ClientSession, cache: TTLCache, lock: Lock):
    url = f'{utils.URL_MEMBERS}/Members/{vi_member.get_id()}/Voting?house={"Commons" if vi_member.is_mp() is True else "Lords"}'
    items = await load_data(url, session)

    voting_list = []

    for item in items:
        entry = VotingEntry(item)
        voting_list.append(entry)

    with lock:
        cache[vi_member.get_id()] = voting_list


