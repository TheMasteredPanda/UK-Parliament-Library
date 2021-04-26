import datetime
from typing import Union
from ..structures.members import PartyMember


class BillStage:
    def __init__(self, json_object):
        self._stage_id = json_object['id']
        self._name = json_object['name']
        self._order = json_object['sortOrder']
        self._category_stage = json_object['stageCategory']
        self._prominent_order = json_object['prominentSortOrder']
        self._house = json_object['house']

    def get_stage_id(self) -> int:
        return self._stage_id

    def get_name(self) -> str:
        return self._name

    def get_order(self) -> str:
        return self._order

    def get_category_stage(self) -> str:
        return self._category_stage

    def get_prominent_order(self) -> int:
        return self._prominent_order

    def get_house(self):
        return self._house


class BillType:
    def __init__(self, json_object):
        self._bill_type_id = json_object['id']
        self._category = json_object['category']
        self._name = json_object['name']
        self._description = json_object['description']
        self._order = json_object['order']

    def get_id(self) -> int:
        return self._bill_type_id

    def get_category(self) -> str:
        return self._category

    def get_name(self) -> str:
        return self._name

    def get_description(self) -> str:
        return self._description

    def get_order(self) -> int:
        return self._order


class Bill:
    def __init__(self, json_object):
        value_object = json_object['value']
        self._bill_id = value_object['billID']
        self._title = value_object['shortTitle']
        self._current_house = value_object['currentHouse']
        self._originating_house = value_object['originatingHouse']
        self._last_update = datetime.datetime.fromisoformat(value_object['lastUpdate'])
        self._defeated = value_object['isDefeated']
        self._withdrawn = value_object['billWithdrawn'] if value_object['billWithdrawn'] is not None else False
        self._bill_type_id = value_object['billType']['id']
        self._sessions = value_object['sessions']
        self._current_stage_id = value_object['currentStage']['stageId']
        self._current_stage_sitting = value_object['currentStage']['stageSitting']
        self._royal_assent = value_object['hasRoyalAssent']
        self._act = value_object['isAct']
        self._sponsors: list[PartyMember] = []
        self._date_introduced = datetime.datetime.fromisoformat(value_object['sessions'][0]['startDate'])

    def get_date_introduced(self) -> Union[datetime.datetime, None]:
        return self._date_introduced

    def set_long_title(self, long_title: str):
        self._long_title = long_title

    def set_sponsors(self, sponsors: list[PartyMember]):
        self._sponsors.extend(sponsors)

    def set_bill_type(self, btype):
        self._bill_type = btype

    def get_long_title(self) -> Union[str, None]:
        return self._long_title

    def get_sponsors(self) -> list[PartyMember]:
        return self._sponsors

    def has_royal_assent(self) -> bool:
        return self._royal_assent

    def is_act(self) -> bool:
        return self._act

    def get_bill_id(self) -> int:
        return self._bill_id

    def get_title(self) -> str:
        return self._title

    def get_current_house(self) -> str:
        return self._current_house
    
    def get_originating_house(self) -> str:
        return self._originating_house

    def get_last_update(self) -> Union[datetime.datetime, None]:
        return self._last_update

    def was_defeated(self) -> bool:
        return self._defeated

    def was_withdrawan(self) -> bool:
        return self._withdrawn

    def get_bill_type(self) -> Union[BillType, None]:
        return self._bill_type

    def get_sessions_accomodated(self) -> list:
        return self._sessions

    def _get_current_stage_id(self):
        return self._current_stage_id

    def set_current_stage(self, current_stage):
        self.current_stage = current_stage

    def get_current_stage(self) -> Union[BillStage, None]:
        return self.current_stage


class LordsDivision:
    def __init__(self, json_object):
        self._division_id = json_object['divisionId']
        self._date = datetime.datetime.fromisoformat(json_object['date'])
        self._division_number = json_object['number']
        self._notes = json_object['notes']
        self._title = json_object['title']
        self._whipped = json_object['isWhipped']
        self._gov_content = json_object['isGovernmentContent']
        self._aye_votes = json_object['tellerContentCount']
        self._no_votes = json_object['tellerNotContentCount']
        self._sponsoring_member_id = json_object['sponsoringMemberId']
        self._is_house = json_object['isHouse']
        self._amendment_motion_notes = json_object['amendmentMotionNotes']
        if self._amendment_motion_notes is not None and self._amendment_motion_notes != '':
            self._amendment_motion_notes = self._amendment_motion_notes.replace('<p>', '').replace('</p>', '')\
                    .replace('<em>', '').replace('<br />', '').replace('</em>', '')
        self._gov_won = json_object['isGovernmentWin']
        self._remote_voting_start = datetime.datetime.fromisoformat(
                                        json_object['remoteVotingStart']
                                    ) if json_object['remoteVotingStart'] is not None else None
        self._remote_voting_end = datetime.datetime.fromisoformat(
                                        json_object['remoteVotingEnd']
                                    ) if json_object['remoteVotingEnd'] is not None else None
        self._aye_teller_ids = list(map(lambda teller: teller['memberId'], json_object['contentTellers']))
        self._no_teller_ids = list(map(lambda teller: teller['memberId'], json_object['notContentTellers']))
        self._aye_member_ids = list(map(lambda lord: lord['memberId'], json_object['contents']))
        self._no_member_ids = list(map(lambda lord: lord['memberId'], json_object['notContents']))
        self._aye_tellers: list[PartyMember] = []
        self._no_tellers: list[PartyMember] = []
        self._aye_members: list[PartyMember] = []
        self._no_members: list[PartyMember] = []
        self._sponsoring_member: Union[PartyMember, None] = None

    def get_id(self) -> int:
        return self._division_id

    def get_amendment_motion_notes(self) -> str:
        return self._amendment_motion_notes

    def get_division_date(self) -> Union[datetime.datetime, None]:
        return self._date

    def get_notes(self):
        return self._notes

    def get_division_title(self):
        return self._title

    def was_whipped(self):
        return self._whipped

    def is_government_content(self):
        return self._gov_content

    def get_aye_count(self) -> int:
        return self._aye_votes

    def get_no_count(self) -> int:
        return self._no_votes

    def get_sponsoring_member(self) -> Union[PartyMember, None]:
        return self._sponsoring_member

    def get_is_house(self):
        return self._is_house()

    def did_government_win(self) -> bool:
        return self._gov_won

    def get_remote_voting_start_date(self) -> Union[datetime.datetime, None]:
        return self._remote_voting_start

    def get_remote_voting_end_date(self) -> Union[datetime.datetime, None]:
        return self._remote_voting_end

    def get_aye_tellers(self) -> list[PartyMember]:
        return self._aye_tellers

    def get_no_tellers(self) -> list[PartyMember]:
        return self._no_tellers

    def get_aye_members(self) -> list[PartyMember]:
        return self._aye_members

    def get_no_members(self) -> list[PartyMember]:
        return self._no_members

    def get_aye_teller_ids(self) -> list[int]:
        return self._aye_teller_ids

    def get_no_teller_ids(self) -> list[int]:
        return self._no_teller_ids

    def get_no_vote_member_ids(self) -> list[int]:
        return self._no_member_ids

    def get_aye_vote_member_ids(self) -> list[int]:
        return self._aye_member_ids

    def get_sponsoring_member_id(self) -> int:
        return self._sponsoring_member_id

    def set_sponsoring_member(self, member: PartyMember):
        self._sponsoring_member = member

    def set_aye_tellers(self, tellers: list[PartyMember]):
        self._aye_tellers = tellers

    def set_no_tellers(self, tellers: list[PartyMember]):
        self._no_tellers = tellers

    def set_aye_members(self, members: list[PartyMember]):
        self._aye_members = members

    def set_no_members(self, members: list[PartyMember]):
        self._no_members = members


class CommonsDivision:
    def __init__(self, json_object):
        self._division_id = json_object['DivisionId']
        self._date = datetime.datetime.fromisoformat(json_object['Date'])
        self._publiciation_uploaded = datetime.datetime.fromisoformat(json_object['PublicationUpdated'])
        self._number = json_object['Number']
        self._deferred = json_object['IsDeferred']
        self._evel_type = json_object['EVELType']
        self._evel_country = json_object['EVELCountry']
        self._title = json_object['Title']
        self._aye_count = json_object['AyeCount']
        self._no_count = json_object['NoCount']
        self._double_majority_aye_count = json_object['DoubleMajorityAyeCount']
        self._double_majority_no_count = json_object['DoubleMajorityNoCount']
        self._aye_teller_ids = [] if json_object['AyeTellers'] is None else\
                list(map(lambda teller_object: teller_object['MemberId'], json_object['AyeTellers']))
        self._no_teller_ids = [] if json_object['NoTellers'] is None else \
                list(map(lambda teller_object: teller_object['MemberId'], json_object['NoTellers']))
        self._aye_ids = list(map(lambda mp: mp['MemberId'], json_object['Ayes']))
        self._no_ids = list(map(lambda mp: mp['MemberId'], json_object['Noes']))
        self._no_vote_ids = list(map(lambda mp: mp['MemberId'], json_object['NoVoteRecorded']))
        self._ayes_members: list[PartyMember] = []
        self._noes_members: list[PartyMember] = []
        self._didnt_vote: list[PartyMember] = []
        self._aye_tellers: list[PartyMember] = []
        self._no_tellers: list[PartyMember] = []

    def get_aye_count(self):
        return self._aye_count

    def get_no_count(self):
        return self._no_count

    def get_id(self) -> int:
        return self._division_id

    def get_division_date(self) -> Union[datetime.datetime, None]:
        return self._date

    def get_publication_uploaded_date(self) -> Union[datetime.datetime, None]:
        return self._publiciation_uploaded

    def get_division_number(self) -> int:
        return self._number

    def was_deferred(self) -> bool:
        return self._deferred

    def get_evel_type(self):
        return self._evel_type

    def get_evel_country(self):
        return self._evel_country

    def get_division_title(self) -> str:
        return self._title

    def ayes(self) -> int:
        return self._aye_count

    def noes(self) -> int:
        return self._no_count

    def supermajority_ayes(self) -> int:
        return self._double_majority_aye_count

    def supermajority_noes(self) -> int:
        return self._double_majority_no_count

    def set_aye_members(self, members: list[PartyMember]):
        self._ayes_members = members

    def set_no_members(self, members: list[PartyMember]):
        self._noes_members = members

    def set_didnt_vote_members(self, members: list[PartyMember]):
        self._didnt_vote = members

    def set_aye_tellers(self, members: list[PartyMember]):
        self._aye_tellers = members

    def set_no_tellers(self, members: list[PartyMember]):
        self._no_tellers = members

    def get_aye_member_ids(self) -> list[int]:
        return self._aye_ids

    def get_no_member_ids(self) -> list[int]:
        return self._no_ids

    def get_didnt_vote_member_ids(self) -> list[int]:
        return self._no_vote_ids

    def get_no_teller_ids(self) -> list[int]:
        return self._no_teller_ids

    def get_aye_teller_ids(self) -> list[int]:
        return self._aye_teller_ids

    def get_aye_members(self) -> list[PartyMember]:
        return self._ayes_members

    def get_no_members(self) -> list[PartyMember]:
        return self._noes_members

    def get_didnt_vote_members(self) -> list[PartyMember]:
        return self._didnt_vote
