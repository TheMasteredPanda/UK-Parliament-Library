from datetime import datetime
from typing import Union
from ..utils import BetterEnum


class GoverningCapacity(BetterEnum):
    """
    Enums representing different types of Government structures. This is for determining
    what sort of party is in Opposition and in Government.
    """

    SINGLE_PARTY_GOVERNMENT = 0
    COALITION_PARTY_GOVERNMENT = 1
    CAS_OPPOSITION_PARTY = 2
    OFFICIAL_OPPOSITION = 3

    @classmethod
    def from_value(cls, value: int):
        for option in cls:
            if option.value == value:
                return value
        raise Exception(f"{value} was not associated with any of the enums")


class VotingEntry:
    def __init__(self, json_object):
        """
        A voting entry is a object representation of a Member's voting history on a division.

        Parameters
        ----------
        json_object: :class:`object`
            A JSON serialized voting history entry.
        """
        value_object = json_object["value"]
        self.house = value_object["house"]
        self.voting_id = value_object["id"]
        self.vote = value_object["inAffirmativeLobby"]
        self.teller = value_object["actedAsTeller"]
        self.division_url = json_object["links"][0]["href"]

    def get_house(self):
        """
        Returns the house the division was taken in (Lords or Commons).
        """
        return self.house

    def get_id(self):
        """
        Returns the entry id.
        """
        return self.voting_id

    def voted_aye(self):
        """
        Returns a :class:`bool` determining if the member voting yes (True) or no (False)
        """
        return self.voted_aye

    def was_teller(self):
        """
        Returns a :class:`bool` determining if the member in this division was also a Tellar (True) or not (False).
        """
        return self.teller

    def get_division_id(self):
        """
        Returns the division id.
        """
        return self.division_url.split("/")[-1].replace(".json", "")


class ElectionResult:
    def __init__(self, json_object):
        """
        An election result in the UK referrs to the local election result of a constitueny. This class therefore
        represents one local election result.

        Parameters
        ----------
        json_object: :class:`object`
            The JSON serialized election result.
        """
        self.result = json_object["result"]
        self.notional = json_object["isNotional"]
        self.electorate = json_object["electorate"]
        self.turnout = json_object["turnout"]
        self.date = datetime.fromisoformat(json_object["electionDate"])
        self.majority = json_object["majority"]
        self.candidates = []

        for candidate_object in json_object["candidates"]:
            candidate_name = candidate_object["name"]
            candidate_party_id = candidate_object["party"]["id"]
            candidate_party_name = candidate_object["party"]["name"]
            vote_share_change = candidate_object["resultChange"]
            candidate_order = candidate_object["rankOrder"]
            votes_received = candidate_object["votes"]
            vote_share = candidate_object["voteShare"]
            self.candidates.append(
                {
                    "name": candidate_name,
                    "party_id": candidate_party_id,
                    "party_name": candidate_party_name,
                    "vote_share_change": vote_share_change,
                    "order": candidate_order,
                    "votes": votes_received,
                    "vote_share": vote_share,
                }
            )

    def get_election_date(self) -> Union[datetime, None]:
        """
        Returns the date of the election.
        """
        return self.date

    def get_result(self) -> str:
        """
        Returns the winning party name.
        """
        return self.result

    def get_notional(self) -> bool:
        """
        Returns whether or not the election was notional (True) or not (False).
        """
        return self.notional

    def get_electorate_size(self) -> int:
        """
        Returns the electorate size (the amount of people who live within a constitueny).
        """
        return self.electorate

    def get_turnout(self) -> int:
        """
        Returns the amount of people who turns out to vote.
        """
        return self.turnout

    def get_majority(self) -> int:
        """
        Returns the majority amount.
        """
        return self.majority

    def get_candidates(self) -> list[dict]:
        """
        Returns a list of candidates. All entries consist of the following information:

        {
            "name": Name of the Candidate.
            "party_id": Candidate Party Id.
            "party_name": Candidate Party Name.
            "vote_share_change": Vote share percentage (as a percentage point).
            "order": Where this candidate landed in the results (1st, 2nd, 3rd, &c).
            "votes": Amount of votes received.
            "vote_share": The amount of votes this candidate makes up in the turnout as a percentage point.
        }

        """
        return self.candidates


class PartyMemberBiography:
    def __init__(self, json_object):
        """
        A party member's biography is the history of the member in public life. The Government, Opposition, and Other
        Posts within public life they have held.

        Parameters
        ----------
        json_object: :class:`object`
            The JSON serialized biography of a member.
        """
        self.representations = []
        self.memberships = []
        self.government_posts = []
        self.opposition_posts = []
        self.other_posts = []
        self.committee_membership = []
        self.party_memberships = []

        value_object = json_object["value"]

        for representation in value_object["representations"]:
            self.representations.append(
                {
                    "house_id": representation["house"],
                    "constituency_name": representation["name"],
                    "id": representation["id"],
                    "started": datetime.fromisoformat(representation["startDate"])
                    if representation["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(representation["endDate"])
                    if representation["endDate"] is not None
                    else None,
                    "additional_notes": representation["additionalInfo"],
                }
            )

        for membership in value_object["houseMemberships"]:
            self.memberships.append(
                {
                    "house_id": membership["house"],
                    "id": membership["id"],
                    "started": datetime.fromisoformat(membership["startDate"])
                    if membership["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(membership["endDate"])
                    if membership["endDate"] is not None
                    else None,
                    "additional_notes": membership["additionalInfo"],
                }
            )

        for post in value_object["governmentPosts"]:
            self.government_posts.append(
                {
                    "house_id": post["house"],
                    "office": post["name"],
                    "id": post["id"],
                    "started": datetime.fromisoformat(post["startDate"])
                    if post["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(post["endDate"])
                    if post["endDate"] is not None
                    else None,
                    "department": post["additionalInfo"],
                }
            )

        for post in value_object["oppositionPosts"]:
            self.opposition_posts.append(
                {
                    "house_id": post["house"],
                    "office": post["name"],
                    "id": post["id"],
                    "started": datetime.fromisoformat(post["startDate"])
                    if post["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(post["endDate"])
                    if post["endDate"] is not None
                    else None,
                }
            )

        for post in value_object["otherPosts"]:
            self.other_posts.append(
                {
                    "house_id": post["house"],
                    "office": post["name"],
                    "id": post["id"],
                    "started": datetime.fromisoformat(post["startDate"])
                    if post["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(post["endDate"])
                    if post["endDate"] is not None
                    else None,
                    "additional_notes": post["additionalInfo"],
                }
            )

        for membership in value_object["committeeMemberships"]:
            self.committee_membership.append(
                {
                    "house_id": membership["house"],
                    "committee": membership["name"],
                    "id": membership["id"],
                    "started": datetime.fromisoformat(membership["startDate"])
                    if membership["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(membership["endDate"])
                    if membership["endDate"] is not None
                    else None,
                    "additional_notes": membership["additionalInfo"],
                }
            )

        for membership in value_object["partyAffiliations"]:
            self.party_memberships.append(
                {
                    "house_id": membership["house"],
                    "name": membership["name"],
                    "started": datetime.fromisoformat(membership["startDate"])
                    if membership["startDate"] is not None
                    else None,
                    "ended": datetime.fromisoformat(membership["endDate"])
                    if membership["endDate"] is not None
                    else None,
                    "additional_notes": membership["additionalInfo"],
                }
            )

    def get_representations(self):
        """
        Returns a list of constituenies the member has represented. Every entry has the following structure:

        {
            "house_id": Id of the House this membership is associated with.
            "constituency_name": Name of the members constitueny.
            "id": Representation id.
            "started": When the membership started.
            "ended": When the membership ended.
            "additional_notes": Any additional notes on the
        }

        """
        return self.representations

    def get_memberships(self):
        """
        Returns a list of other memberships this member has had. Every entry has the following structure:

        {
            "house_id": Id of the House the membership is associated with.
            "id": Membership id.
            "started": When the membership started.
            "ended": When the membership ended.
            "additional_notes": Any additional notes.
        }

        """
        return self.memberships

    def get_government_posts(self):
        """
        Returns a list of Government posts this member has held. Every entry has the following structure:

        {
            "house_id": Id of the House the post is associated with.
            "office": Name of the office.
            "id": Post id.
            "started": When the member started the post.
            "ended": When the member left the post.
            "department": Any additional notes.
        }

        """
        return self.government_posts

    def get_oppositions_posts(self):
        """
        Returns a list of Opposition posts this member has held.

        {
            "house_id": Id of the House the post is associated with.
            "office": Name of the office.
            "id": Post id
            "started": When the member started the post.
            "ended": When the member left the post.
        }

        """
        return self.opposition_posts

    def get_other_posts(self):
        """
        Returns a list of Other posts this member has held. Every entry has the following structure:

        {
            "house_id": Id of the House the post is associated with.
            "office": Name of the office.
            "id": Post id.
            "started": When the member started the post.
            "ended": When the member left that post.
            "additional_notes": Any additional notes.
        }

        """
        return self.other_posts

    def get_party_affiliations(self):
        """
        Returns a list of party memberships this member has had. Every entry has the following structure:

        {
            "house_id": Id of the House the post is associated with.
            "name": Name of the party.
            "started": When the membership started.
            "ended": When the membership ended.
            "additional_notes": Any additional notes.
        }

        """
        return self.party_memberships

    def get_committee_memberships(self):
        """
        Returns a list of committee memberships this member has had. Every entry has the following structure:

        {
            "house_id": Id of the House the post is associated with.
            "committee": Committee name.
            "id": Membership id.
            "started": When the membership started.
            "ended": When the membership ended.
            "additional_notes": Any additional notes.
        }

        """
        return self.committee_membership


class PartyMember:
    def __init__(self, json_object):
        """
        A party member is a member of a party - a political party being a group of politicians with the same agenda
        working as a block. This class represents one Party Member.
        """
        value_object = json_object["value"]
        self._member_id = value_object["id"]
        self._titled_name = value_object["nameFullTitle"]
        self._addressed_name = value_object["nameAddressAs"]
        self._displayed_name = value_object["nameDisplayAs"]
        self._listed_name = value_object["nameListAs"]
        self._party_id = value_object["latestParty"]["id"]
        self._gender = value_object["gender"]
        self._started = datetime.fromisoformat(
            value_object["latestHouseMembership"]["membershipStartDate"]
        )
        self._thumbnail = value_object["thumbnailUrl"]
        self._house_id = value_object["latestHouseMembership"]["house"]
        self._membership_from = value_object["latestHouseMembership"]["membershipFrom"]
        self._membership_id = value_object["latestHouseMembership"]["membershipFromId"]

    def get_biography(self) -> Union[PartyMemberBiography, None]:
        """
        Returns the biography of the member.
        """
        return self._biography

    def _set_biography(self, bio: PartyMemberBiography):
        """
        Sets the biography of the member.

        Parameters
        ----------
        bio: :class:`PartyMemberBiography`
            The biography instance.
        """
        self._biography = bio

    def get_thumbnail_url(self):
        """
        Returns the link to the members thumbnail image.
        """
        return self._thumbnail

    def _get_membership_from_id(self) -> int:
        """
        Returns the id of the membership the member has (party id).
        """
        return self._membership_id

    def get_membership_from(self) -> str:
        """
        Returns the constitueny name of the member is they're a Member of Parliament. If not
        this will show the title the member has.
        """
        return self._membership_from

    def get_membership_id(self) -> str:
        """
        Returns the id of the mbmership the member has (party id).
        """
        return self._membership_id

    def is_mp(self) -> bool:
        """
        Returns a :class:`bool` determining if the member is a Member of Parliament (True) or not (False)
        """
        return self._house_id != 2

    def get_house(self) -> int:
        """
        Retursn the name of the house the member is in (Lords or Commons).
        """
        return self._house_id

    def get_id(self) -> int:
        """
        Returns the member's id.
        """
        return self._member_id

    def get_titled_name(self) -> str:
        """
        Returns the members title.
        """
        return self._titled_name

    def get_display_name(self) -> str:
        """
        Returns the display name of the member.
        """
        return self._displayed_name

    def get_addressed_name(self) -> str:
        """
        Returns the name of the member as addressed in the House.
        """
        return self._addressed_name

    def get_listed_name(self) -> str:
        """
        Returns the name of the member as listed on documents.
        """
        return self._listed_name

    def get_party_id(self) -> int:
        """
        Returns the party id the member is affiliated with.
        """
        return self._party_id

    def get_gender(self) -> str:
        """
        Returns the gender of the member.
        """
        return self._gender

    def get_started_date(self) -> Union[datetime, None]:
        """
        Returns the date the member started public life in the UK.
        """
        return self._started


class Party:
    def __init__(self, json_object):
        """
        A party is a group of members within the Houses of Parliament that act as one block with one agenda.
        This class is the representation of a Party.

        Parameters
        ----------
        json_object: :class:`object`
            A JSON serialized party object.
        """
        value_object = json_object["value"]
        self._party_id = value_object["id"]
        self._name = value_object["name"]
        self._abbreviation = value_object["name"]
        self._primary_colour = value_object["backgroundColour"]
        self._secondary_colour = value_object["foregroundColour"]
        self._lords_govt_party = value_object["isLordsMainParty"]
        self._lords_party = self._lords_govt_party
        self._lords_spiritual_party = value_object["isLordsSpiritualParty"]
        self._governing = value_object["governmentType"] is not None
        self._governing_capacity = (
            GoverningCapacity.from_value(value_object["governmentType"])
            if json_object["value"]["governmentType"] is not None
            else None
        )
        self._independent_group = value_object["isIndependentParty"]
        self._hoc_members = []
        self._hol_members = []

    def add_member(self, member: PartyMember):
        """
        Add a member to the party.

        Parameters
        ----------
        member: :class:`PartyMember`
            A party member.
        """
        if member.get_house() == 2:
            self._hol_members.append(member)
        else:
            self._hoc_members.append(member)

    def set_lords_party(self, lords_party: bool = True):
        """
        Set the :class:`bool` of this Party object to signify that this is both a Commons and Lords party.

        Parameters
        ----------
        lords_party: :class:`bool`
            Set whether or not this party is also a Lords party (True) or not (False)
        """
        self._lords_party = lords_party

    def get_name(self) -> str:
        """
        Returns party name
        """
        return self._name

    def get_party_id(self) -> int:
        """
        Returns party id.
        """
        return self._party_id

    def get_all_members(self) -> list[PartyMember]:
        """
        Returns all members of this party.
        """
        members = self._hoc_members.copy()
        members.extend(self._hol_members.copy())
        return members

    def get_mps(self) -> list[PartyMember]:
        """
        Returns Commons members only.
        """
        return self._hoc_members

    def get_lords(self) -> list[PartyMember]:
        """
        Returns Lords members only.
        """
        return self._hol_members

    def get_primary_party_colour(self):
        """
        Returns the primary colour of the party.
        """
        return self._primary_colour

    def get_secondary_party_colour(self):
        """
        Returns the secondary colour of the party.
        """
        return self._secondary_colour

    def get_abber(self):
        """
        Returns the abbreviation of the parties full name.
        """
        return self._abbreviation

    def find_member_by_name(self, name: str) -> Union[PartyMember, None]:
        """
        Find a member by their name.

        Parameters
        ----------
        name: :class:`str`
            The name of a potential member in this party.

        Returns
        -------
        :class:`Union[PartyMember, None]`
            A party member instance or None.
        """
        for member in self.get_all_members():
            if (
                name in member.get_display_name()
                or name in member.get_titled_name()
                or name in member.get_addressed_name()
            ):
                return member
        return None
