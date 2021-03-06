import datetime
import json
from typing import Union
from ..structures.members import PartyMember


class BillStage:
    def __init__(self, json_object):
        """
        A bill stage is a stage in the legislative process that a bill will likely have to go through
        in order to be, ultimately, passed by Parliament. This class is used to serialize a bill stage.

        Parameters
        ----------
        json_object: :class:`object`
            The JSON serialized bill stage.
        """
        self._stage_id = json_object["id"]
        self._name = json_object["name"]
        self._order = (
            json_object["sortOrder"] if "sortOrder" in json_object.keys() else ""
        )
        self._category_stage = (
            json_object["stageCategory"]
            if "stageCategory" in json_object.keys()
            else ""
        )
        self._prominent_order = (
            json_object["prominentSortOrder"]
            if "prominentSortOrder" in json_object.keys()
            else -1
        )
        self._house = json_object["house"]

    def get_stage_id(self) -> int:
        """
        Returns the bill stage id.
        """
        return self._stage_id

    def get_name(self) -> str:
        """
        Returns the bill stage name.
        """
        return self._name

    def get_order(self) -> str:
        """
        Returns the bill stage order.
        """
        return self._order

    def get_category_stage(self) -> str:
        """
        Returns the bill stage category.
        """
        return self._category_stage

    def get_prominent_order(self) -> int:
        """
        Returns the bill stage prominent order.
        """
        return self._prominent_order

    def get_house(self):
        """
        Returns the house in which this bill stage is
        associatd with.
        """
        return self._house


class BillType:
    def __init__(self, json_object):
        """
        A class representing a bill type.

        Parameters
        ----------
        json_object: :class:`object`
            A JSON serialized bill type.
        """
        self._bill_type_id = json_object["id"]
        self._category = json_object["category"]
        self._name = json_object["name"]
        self._description = json_object["description"]
        self._order = json_object["order"] if "order" in json_object.keys() else -1

    def get_id(self) -> int:
        """
        Returns the bill type id.
        """
        return self._bill_type_id

    def get_category(self) -> str:
        """
        Returns the category id.
        """
        return self._category

    def get_name(self) -> str:
        """
        Returns the bill type name.
        """
        return self._name

    def get_description(self) -> str:
        """
        Returns the bill type description
        """
        return self._description

    def get_order(self) -> int:
        """
        Returns the bill type order.
        """
        return self._order


class Bill:
    def __init__(self, json_object):
        """
        A bill is a piece of legislation that is introduced, and 'processed' through the Houses of Parliament.
        This class represents one bill.

        Parameters
        ----------
        json_object: :class:`object`
            A JSON serialized bill.
        """
        value_object = (
            json_object["value"] if "value" in json_object.keys() else json_object
        )
        self._bill_id = value_object["billId"]
        self._title = value_object["shortTitle"]
        self._current_house = value_object["currentHouse"]
        self._originating_house = value_object["originatingHouse"]
        self._last_update = datetime.datetime.strptime(
            value_object["lastUpdate"].split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )
        self._defeated = value_object["isDefeated"]
        self._withdrawn = (
            value_object["billWithdrawn"]
            if value_object["billWithdrawn"] is not None
            else False
        )
        self._bill_type_id = value_object["billTypeId"]
        self._sessions = value_object["includedSessionIds"]
        self._current_stage_id = value_object["currentStage"]["stageId"]
        self._stage_sittings = value_object["currentStage"]["stageSittings"]
        self._royal_assent = self._current_stage_id == 11
        self._act = value_object["isAct"]
        self._sponsors: list[PartyMember] = []
        self._session_introduced = value_object["introducedSessionId"]

    def get_session_introduced_id(self) -> int:
        """
        Returns the session introduced id.
        """
        return self._session_introduced

    def set_long_title(self, long_title: str):
        """
        Sets the long form title of the bill.

        Parameters
        ----------
        long_title: :class:`str`
        """
        self._long_title = long_title

    def set_sponsors(self, sponsors: list[PartyMember]):
        """
        Sets the sponsors of the bill.

        Parameters
        ----------
        sponsors: :class:`list[PartyMember]`
            A list of sponsors.
        """
        self._sponsors.extend(sponsors)

    def set_bill_type(self, btype):
        """
        Sets the bill's type.

        Parameters
        ----------
        btype: :class:`BillType`
            The bill type.
        """
        self._bill_type = btype

    def get_long_title(self) -> Union[str, None]:
        """
        Returns the long term title of the bill.
        """
        return self._long_title

    def get_sponsors(self) -> list[PartyMember]:
        """
        Returns the list of bill sponsors.
        """
        return self._sponsors

    def has_royal_assent(self) -> bool:
        """
        Returns a :class:`bool` determining if the bill has received Royal Assent (True) or not (False).
        """
        return self._royal_assent

    def is_act(self) -> bool:
        """
        Returns a :class:`bool` determining if the bill is an act (True) or not (False).
        """
        return self._act

    def get_bill_id(self) -> int:
        """
        Returns the bill id.
        """
        return self._bill_id

    def get_title(self) -> str:
        """
        Returns the short form title of the bill.
        """
        return self._title

    def get_current_house(self) -> str:
        """
        Returns the current house the bill is in (Lords or Commons).
        """
        return self._current_house

    def get_originating_house(self) -> str:
        """
        Returns the house the bill was introduced in (Lords or Commons).
        """
        return self._originating_house

    def get_last_update(self) -> Union[datetime.datetime, None]:
        """
        Returns the last update to the bill.
        """
        return self._last_update

    def was_defeated(self) -> bool:
        """
        Returns a :class:`bool` determining if the bill has been defeated (True) or not (False).
        """
        return self._defeated

    def was_withdrawan(self) -> bool:
        """
        Returns a :class:`bool` determining if the bill was withdrawan (True) or not (False).
        """
        return self._withdrawn

    def get_bill_type(self) -> Union[BillType, None]:
        """
        Returns the bill type of the bill.
        """
        return self._bill_type

    def get_sessions_accomodated(self) -> list:
        """
        Returns the ids of the Parliamentary session that the bill has been in.
        """
        return self._sessions

    def get_current_stage_id(self):
        """
        Returns the current bill stage's id..
        """
        return self._current_stage_id

    def set_current_stage(self, current_stage):
        """
        Sets the current bill stage.

        Parameters
        ----------
        current_stage: :class:`BillStage`
            The bill stage to set.
        """
        self._current_stage = current_stage

    def get_current_stage(self) -> Union[BillStage, None]:
        """
        Returns the stage of the bill.
        """
        return self._current_stage


class LordsDivision:
    def __init__(self, json_object):
        """
        A lords division is a vote upon a motion, bill, amendment, &c in the House of Lords.
        This class represents that division.

        Parameters
        ----------
        json_object: :class:`object`
            The JSON serialized division object.
        """
        self._division_id = json_object["divisionId"]
        self._date = datetime.datetime.fromisoformat(json_object["date"])
        self._division_number = json_object["number"]
        self._notes = json_object["notes"]
        self._title = json_object["title"]
        self._whipped = json_object["isWhipped"]
        self._gov_content = json_object["isGovernmentContent"]
        self._aye_votes = json_object["tellerContentCount"]
        self._no_votes = json_object["tellerNotContentCount"]
        self._sponsoring_member_id = json_object["sponsoringMemberId"]
        self._is_house = json_object["isHouse"]
        self._amendment_motion_notes = json_object["amendmentMotionNotes"]
        if (
            self._amendment_motion_notes is not None
            and self._amendment_motion_notes != ""
        ):
            self._amendment_motion_notes = (
                self._amendment_motion_notes.replace("<p>", "")
                .replace("</p>", "")
                .replace("<em>", "")
                .replace("<br />", "")
                .replace("</em>", "")
            )
        self._gov_won = json_object["isGovernmentWin"]
        self._remote_voting_start = (
            datetime.datetime.fromisoformat(json_object["remoteVotingStart"])
            if json_object["remoteVotingStart"] is not None
            else None
        )
        self._remote_voting_end = (
            datetime.datetime.fromisoformat(json_object["remoteVotingEnd"])
            if json_object["remoteVotingEnd"] is not None
            else None
        )
        self._aye_teller_ids = list(
            map(lambda teller: teller["memberId"], json_object["contentTellers"])
        )
        self._no_teller_ids = list(
            map(lambda teller: teller["memberId"], json_object["notContentTellers"])
        )
        self._aye_member_ids = list(
            map(lambda lord: lord["memberId"], json_object["contents"])
        )
        self._no_member_ids = list(
            map(lambda lord: lord["memberId"], json_object["notContents"])
        )
        self._aye_tellers: list[PartyMember] = []
        self._no_tellers: list[PartyMember] = []
        self._aye_members: list[PartyMember] = []
        self._no_members: list[PartyMember] = []
        self._sponsoring_member: Union[PartyMember, None] = None

    def get_id(self) -> int:
        """
        Returns the division id.
        """
        return self._division_id

    def get_amendment_motion_notes(self) -> str:
        """
        Returns the division  motion notes.
        """
        return self._amendment_motion_notes

    def get_division_date(self) -> Union[datetime.datetime, None]:
        """
        Returns the date the division was taken.
        """
        return self._date

    def get_notes(self):
        """
        Returns the notes of the division.
        """
        return self._notes

    def get_division_title(self):
        """
        Returns the division title.
        """
        return self._title

    def was_whipped(self):
        """
        Returns a :class:`bool` determining if the division was whipped (True) or not (False).
        """
        return self._whipped

    def is_government_content(self):
        """
        Returns a :class:`bool` determining if the division was for Government content (True) or not (False).
        """
        return self._gov_content

    def get_aye_count(self) -> int:
        """
        Returns a :class:`int` total of members who voted yes.
        """
        return self._aye_votes

    def get_no_count(self) -> int:
        """
        Returns a :class:`int` total of members who voted no.
        """
        return self._no_votes

    def get_sponsoring_member(self) -> Union[PartyMember, None]:
        """
        Returns a list of sponsors.
        """
        return self._sponsoring_member

    def get_is_house(self):
        """
        Unsure.
        """
        return self._is_house()

    def did_government_win(self) -> bool:
        """
        Returns a :class:`bool` determining if the Government won the division (True) or not (False)
        """
        return self._gov_won

    def get_remote_voting_start_date(self) -> Union[datetime.datetime, None]:
        """
        Returns the date when the remote voting count started (proxy voting).
        """
        return self._remote_voting_start

    def get_remote_voting_end_date(self) -> Union[datetime.datetime, None]:
        """
        Returns the date when the remote count stopped (proxy voting).
        """
        return self._remote_voting_end

    def get_aye_tellers(self) -> list[PartyMember]:
        """
        Returns a list of :class:`PartyMember` instances who were Tellers for the Yes votes.
        """
        return self._aye_tellers

    def get_no_tellers(self) -> list[PartyMember]:
        """
        Returns a list of :class:`PartyMember` instances who were Tellers for the No votes.
        """
        return self._no_tellers

    def get_aye_members(self) -> list[PartyMember]:
        """
        Returns a list of :class:`PartyMember` instances who voted Yes.
        """
        return self._aye_members

    def get_no_members(self) -> list[PartyMember]:
        """
        Returns a list of :class:`PartyMember` instances for voted No.
        """
        return self._no_members

    def get_aye_teller_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who were Tellers for the Yes vote.
        """
        return self._aye_teller_ids

    def get_no_teller_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who were Tellers for the No vote.
        """
        return self._no_teller_ids

    def get_no_vote_member_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who voted No.
        """
        return self._no_member_ids

    def get_aye_vote_member_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who voted Yes.
        """
        return self._aye_member_ids

    def get_sponsoring_member_id(self) -> int:
        """
        Returns the member who sponsored the bill.
        """
        return self._sponsoring_member_id

    def set_sponsoring_member(self, member: PartyMember):
        """
        Set the sponsoring member.

        Parameters
        ----------
        member: :class:`PartyMember`
            The sponsoring member.
        """
        self._sponsoring_member = member

    def set_aye_tellers(self, tellers: list[PartyMember]):
        """
        Set the aye Tellars.

        Parameters
        ----------
        tellers: :class:`list[PartyMember]`
            The tellars for the Yes vote.
        """
        self._aye_tellers = tellers

    def set_no_tellers(self, tellers: list[PartyMember]):
        """
        Set the no Tellars.

        Parameters
        ----------
        tellers: :class:`list[PartyMember]`
            The tellars for the No vote.
        """
        self._no_tellers = tellers

    def set_aye_members(self, members: list[PartyMember]):
        """
        Set Aye members.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            The members who voted yes.
        """
        self._aye_members = members

    def set_no_members(self, members: list[PartyMember]):
        """
        Set No members.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            The members who voted no.
        """
        self._no_members = members


class CommonsDivision:
    def __init__(self, json_object):
        """
        A commons division is a vote upon a motion, bill, amendment, &c in the House of Commons.
        This class represents that division.

        Parameters
        ----------
        json_object: :class:`object`
            The JSON serialized division object.
        """
        self._division_id = json_object["DivisionId"]
        self._date = datetime.datetime.fromisoformat(json_object["Date"])
        self._publiciation_uploaded = datetime.datetime.fromisoformat(
            json_object["PublicationUpdated"]
        )
        self._number = json_object["Number"]
        self._deferred = json_object["IsDeferred"]
        self._evel_type = json_object["EVELType"]
        self._evel_country = json_object["EVELCountry"]
        self._title = json_object["Title"]
        self._aye_count = json_object["AyeCount"]
        self._no_count = json_object["NoCount"]
        self._double_majority_aye_count = json_object["DoubleMajorityAyeCount"]
        self._double_majority_no_count = json_object["DoubleMajorityNoCount"]
        self._aye_teller_ids = (
            []
            if json_object["AyeTellers"] is None
            else list(
                map(
                    lambda teller_object: teller_object["MemberId"],
                    json_object["AyeTellers"],
                )
            )
        )
        self._no_teller_ids = (
            []
            if json_object["NoTellers"] is None
            else list(
                map(
                    lambda teller_object: teller_object["MemberId"],
                    json_object["NoTellers"],
                )
            )
        )
        self._aye_ids = list(map(lambda mp: mp["MemberId"], json_object["Ayes"]))
        self._no_ids = list(map(lambda mp: mp["MemberId"], json_object["Noes"]))
        self._no_vote_ids = list(
            map(lambda mp: mp["MemberId"], json_object["NoVoteRecorded"])
        )
        self._ayes_members: list[PartyMember] = []
        self._noes_members: list[PartyMember] = []
        self._didnt_vote: list[PartyMember] = []
        self._aye_tellers: list[PartyMember] = []
        self._no_tellers: list[PartyMember] = []

    def get_aye_count(self) -> int:
        """
        Returns a :class:`int` total of members who voted Yes.
        """
        return self._aye_count

    def get_no_count(self) -> int:
        """
        Returns a :class:`int` total of members who voted No.
        """
        return self._no_count

    def get_id(self) -> int:
        """
        Returns division id.
        """
        return self._division_id

    def get_division_date(self) -> Union[datetime.datetime, None]:
        """
        Returns the date the division was taken.
        """
        return self._date

    def get_publication_uploaded_date(self) -> Union[datetime.datetime, None]:
        """
        Returns the date the division publication was uploaded.
        """
        return self._publiciation_uploaded

    def get_division_number(self) -> int:
        """
        Returns the division number.
        """
        return self._number

    def was_deferred(self) -> bool:
        """
        Returns a :class:`bool` determining if the division was deferred (True) or not (False)
        """
        return self._deferred

    def get_evel_type(self):
        """
        Returns the evel type.
        """
        return self._evel_type

    def get_evel_country(self):
        """
        Returns the evel country.
        """
        return self._evel_country

    def get_division_title(self) -> str:
        """
        Returns the division title.
        """
        return self._title

    def supermajority_ayes(self) -> int:
        """
        Returns a :class:`int` determining if the division was a supermajority of ayes.
        """
        return self._double_majority_aye_count

    def supermajority_noes(self) -> int:
        """
        Returns a :class:`int` determining if the division was a supermajority of noes.
        """
        return self._double_majority_no_count

    def set_aye_members(self, members: list[PartyMember]):
        """
        Set aye voting members.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            The members who voted Yes.
        """
        self._ayes_members = members

    def set_no_members(self, members: list[PartyMember]):
        """
        Set no voting members.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            The members who voted No.
        """
        self._noes_members = members

    def set_didnt_vote_members(self, members: list[PartyMember]):
        """
        Set members who didn't vote.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            The members who didn't vote.
        """
        self._didnt_vote = members

    def set_aye_tellers(self, members: list[PartyMember]):
        """
        Set aye Tellars.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            Tellars for the Ayes.
        """
        self._aye_tellers = members

    def set_no_tellers(self, members: list[PartyMember]):
        """
        Sye no Tellars.

        Parameters
        ----------
        members: :class:`list[PartyMember]`
            Tellars for the Noes.
        """
        self._no_tellers = members

    def get_aye_member_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who voted Yes.
        """
        return self._aye_ids

    def get_no_member_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who voted No.
        """
        return self._no_ids

    def get_didnt_vote_member_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the members who didn't vote.
        """
        return self._no_vote_ids

    def get_no_teller_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the Tellars for the Noes.
        """
        return self._no_teller_ids

    def get_aye_teller_ids(self) -> list[int]:
        """
        Returns a list of :class:`int` associated with the Tellars for the Ayes.
        """
        return self._aye_teller_ids

    def get_aye_members(self) -> list[PartyMember]:
        """
        Returns a list of members who voted Yes.
        """
        return self._ayes_members

    def get_no_members(self) -> list[PartyMember]:
        """
        Reutrns a list of members who voted No.
        """
        return self._noes_members

    def get_didnt_vote_members(self) -> list[PartyMember]:
        """
        Returns a list of members who didn't vote.
        """
        return self._didnt_vote
