from threading import Lock
from cachetools import TTLCache
from enum import Enum
import datetime
import aiohttp
import dateparser
from typing import Union
from .. import utils
from ..utils import BetterEnum, load_data


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

class ElectionResult:
    def __init__(self, json_object):
        self.result = json_object['result']
        self.notional = json_object['isNotional']
        self.electorate = json_object['electorate']
        self.turnout = json_object['turnout']
        self.date = dateparser.parse(json_object['electionDate'])
        self.majority = json_object['majority']
        self.candidates = []

        for candidate_object in json_object['candidates']:
            candidate_name = candidate_object['name']
            candidate_party_id = candidate_object['party']['id']
            candidate_party_name = candidate_object['party']['name']
            vote_share_change = candidate_object['resultChange']
            candidate_order = candidate_object['rankOrder']
            votes_received = candidate_object['votes']
            vote_share = candidate_object['voteShare']
            self.candidates.append({'name': candidate_name, 'party_id': candidate_party_id, 'party_name': candidate_party_name, 'vote_share_change': vote_share_change, 'order': candidate_order, 'votes': votes_received, 'vote_share': vote_share})

    def get_election_date(self) -> Union[datetime.datetime, None]:
        return self.date

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

class PartyMemberBiography:
    def __init__(self, json_object):
        self.representations = []
        self.memberships = []
        self.government_posts = []
        self.opposition_posts = []
        self.other_posts = []
        self.committee_membership = []
        self.party_memberships = []

        value_object = json_object['value']

        for representation in value_object['representations']:
            self.representations.append({'house_id': representation['house'], 'constituency_name': representation['name'], 'id': representation['id'], 'started': dateparser.parse(representation['startDate']) if representation['startDate'] is not None else None, 'ended': dateparser.parse(representation['endDate']) if representation['endDate'] is not None else None, 'additional_notes': representation['additionalInfo']})

        for membership in value_object['houseMemberships']:
            self.memberships.append({'house_id': membership['house'], 'id': membership['id'], 'started': dateparser.parse(membership['startDate']) if membership['startDate'] is not None else None, 'ended': dateparser.parse(membership['endDate']) if membership['endDate'] is not None else None, 'additional_notes': membership['additionalInfo']})

        for post in value_object['governmentPosts']:
            self.government_posts.append({'house_id': post['house'], 'office': post['name'], 'id': post['id'], 'started': dateparser.parse(post['startDate']) if post['startDate'] is not None else None, 'ended': dateparser.parse(post['endDate']) if post['endDate'] is not None else None, 'department': post['additionalInfo']})

        for post in value_object['oppositionPosts']:
            self.opposition_posts.append({'house_id': post['house'], 'office': post['name'], 'id': post['id'], 'started': dateparser.parse(post['startDate']) if post['startDate'] is not None else None, 'ended': dateparser.parse(post['endDate']) if post['endDate'] is not None else None})

        for post in value_object['otherPosts']:
            self.other_posts.append({'house_id': post['house'], 'office': post['name'], 'id': post['id'], 'started': dateparser.parse(post['startDate']) if post['startDate'] is not None else None, 'ended': dateparser.parse(post['endDate']) if post['endDate'] is not None else None, 'additional_notes': post['additionalInfo']})
        

        for membership in value_object['committeeMemberships']:
            self.committee_membership.append({'house_id': membership['house'], 'committee': membership['name'], 'id': membership['id'], 'started': dateparser.parse(membership['startDate']) if membership['startDate'] is not None else None, 'ended': dateparser.parse(membership['endDate']) if membership['endDate'] is not None else None, 'additional_notes': membership['additionalInfo']})

        for membership in value_object['partyAffiliations']:
            self.party_memberships.append({'house_id': membership['house'], 'name': membership['name'], 'started': dateparser.parse(membership['startDate']) if membership['startDate'] is not None else None, 'ended': dateparser.parse(membership['endDate']) if membership['endDate'] is not None else None, 'additional_notes': membership['additionalInfo']})

    def get_representations(self):
        return self.representations

    def get_memberships(self):
        return self.memberships

    def get_government_posts(self):
        return self.government_posts

    def get_oppositions_posts(self):
        return self.opposition_posts

    def get_other_posts(self):
        return self.other_posts

    def get_party_affiliations(self):
        return self.party_memberships

    def get_committee_memberships(self):
        return self.committee_membership

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
        self.biography = None


    def get_biography(self) -> Union[PartyMemberBiography, None]:
        return self.biography

    def _set_biography(self, bio: PartyMemberBiography):
        self.biography = bio

    def get_thumbnail_url(self):
        return self.thumbnail

    def _get_membership_from_id(self) -> int:
        return self._membership_id

    def get_membership_from(self) -> str:
        return self.membership_from #If it is a Lord then this will show the Lords membership status (life, hereditary, &c). If this is a commons member this will show the constitueny the member is representing.

    def _get_membership_id(self) -> str:
        return self._membership_id #Should only be relevant to commons members. Should be the constitueny id

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

    def get_primary_party_colour(self):
        return self.primary_colour

    def get_secondary_party_colour(self):
        return self.secondary_colour

    def get_abber(self):
        return self.abbreviation

    def find_member_by_name(self, name: str) -> Union[PartyMember, None]:
        for member in self.get_all_members():
            if name in member.get_display_name() or name in member.get_titled_name() or name in member.get_addressed_name():
                return member
        return None

