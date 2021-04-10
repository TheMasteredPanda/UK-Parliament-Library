from enum import Enum
from typing import Union
from utils import BetterEnum

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

class LatestElectionResult():
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

    def get_result(self):
        return self.result

    def get_notional(self):
        return self.notional

    def get_electorate_size(self):
        return self.electorate

    def get_turnout(self):
        return self.turnout

    def get_majority(self):
        return self.majority

    def get_candidates(self):
        return self.candidates
        
class PartyMember():
    def __init__(self, json_object):
        value_object = json_object['value']
        self.member_id = value_object['id']
        self.titled_name = value_object['nameFullTitle']
        self.addressed_name = value_object['nameAddressAs']
        self.displayed_name = value_object['nameDisplayAs']
        self.listed_name = value_object['nameListAs']
        self._party_id = value_object['latestParty']['id']
        self.gender = value_object['gender']
        self.started = value_object['latestHouseMembership']['membershipStartDate']
        self.thumbnail = value_object['thumbnailUrl']
        self._house_id = value_object['latestHouseMembership']['house']
        self.membership_from = value_object['latestHouseMembership']['membershipFrom']
        self._membership_id = value_object['latestHouseMembership']['membershipFromId']
        self.latest_election_result = None

    def _set_latest_election_result(self, result: LatestElectionResult):
        self.latest_election_result = result

    def _get_membership_from_id(self):
        return self._membership_id

    def get_latest_election_result(self):
        return self.latest_election_result

    def get_membership_from(self):
        return self.membership_from #If it is a Lord then this will show the Lords membership status (life, hereditary, &c). If this is a commons member this will show the constitueny the member is representing.

    def is_mp(self):
        return self._house_id != 2

    def _get_house(self):
        return self._house_id

    def get_id(self):
        return self.member_id

    def get_titled_name(self):
        return self.titled_name

    def get_display_name(self):
        return self.displayed_name
    
    def get_addressed_name(self):
        return self.addressed_name

    def get_listed_name(self):
        return self.listed_name

    def _get_party_id(self):
        return self._party_id

    def get_gender(self):
        return self.gender

    def get_started_date(self):
        return self.started

class Party():
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

    def get_name(self):
        return self.name

    def get_party_id(self):
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

