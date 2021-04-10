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
            if cls.value == value:
                return value
        raise Exception(f'{value} was not associated with any of the enums')
    
class PartyMember():
    def __init__(self, json_object):
        self.member_id = json_object['value']['id']
        self.titled_name = json_object['value']['nameFullTitle']
        self.addressed_name = json_object['value']['nameAddressAs']
        self.displayed_name = json_object['value']['nameDisplayAs']
        self.listed_name = json_object['value']['nameListAs']
        self._party_id = json_object['value']['latestParty']['id']
        self.gender = json_object['value']['gender']
        self.started = json_object['value']['latestHouseMembership']['membershipStartDate']
        self.thumbnail = json_object['value']['thumbnailUrl']
        self._house_id = json_object['value']['lastestHouseMembership']['house']
        self.membership_from = json_object['value']['lastestHouseMembership']['membershipFrom']
        self._membership_id = json_object['value']['latestHouseMembership']['membershipFromId']

    def _get_membership_from_id(self):
        return self._membership_id

    def get_membership_from(self):
        return self.membership_from #If it is a Lord then this will show the Lords membership status (life, hereditary, &c). If this is a commons member this will show the constitueny the member is representing.

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
        self.party_id = json_object['value']['id']
        self.name  = json_object['value']['name']
        self.abbreviation = json_object['value']['name']
        self.primary_colour = json_object['value']['backgroundColour']
        self.secondary_colour = json_object['value']['foregroundColour']
        self.lords_govt_party = json_object['value']['isLordsMainParty']
        self.lords_party = self.lords_govt_party
        self.lords_spiritual_party = json_object['value']['isLordsSpiritualParty']
        self.governing = json_object['value']['governmentType'] is not None
        self.governing_capacity = GoverningCapacity.from_value(json_object['value']['governmentType'])
        self.independent_group = json_object['value']['isIndependentParty']
        self.members = {'hoc': [], 'hol': []}

    def add_member(self, member: PartyMember):
        if len(list(filter(lambda m: m._get_party_id() == member._get_party_id(), self.members['hoc'] if hoc is True else self.members['hol']))) > 0: return
        self.members['hoc'].append(member) if member._get_party_id() == 1 else self.members['hol'].append(member)
    
    def _set_lords_party(self, lords_party: bool = True):
        self.lords_party = lords_party

    def get_name(self):
        return self.name

    def get_party_id(self):
        return self.party_id

    def get_all_members(self) -> list[PartyMember]:
        members = self.members['hoc']
        members.extend(self.members['hol'])
        return members

    def get_mps(self) -> list[PartyMember]:
        return self.members['hoc']

    def get_lords(self) -> list[PartyMember]:
        return self.members['hol']

    def find_member_by_name(self, name: str) -> Union[PartyMember, None]:
        for member in self.get_all_members():
            if name in member.get_display_name() or name in member.get_titled_name() or name in member.get_addressed_name():
                return member
        return None

    def find_member_by_constituency_postcode(self, postcode: str) -> Union[PartyMember, None]:
        pass

