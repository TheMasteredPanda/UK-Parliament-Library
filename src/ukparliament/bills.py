from .structures.bills import Bill, BillStage, BillType, PartyMember
import aiohttp
from . import utils
import json


async def division_task(instance, m_id, member_list: list[PartyMember]):
    """
    A task used to lazily load a member if a member from a :class:`LordsDivision` or :class:`CommonsDivision` is not found in the indexed :class:`PartyMember` list.

    Parameters
    ----------
    m_id: :class:`int`
        Member id.
    member_list: :class:`list`
        A list of party members to add the member to.

    """
    member = instance.get_member_by_id(m_id)
    if member is None:
        member = await instance.lazy_load_member(m_id)
    if member is None:
        raise Exception(f"Couldn't find member {m_id}")
    member_list.append(member)


async def _meta_bill_task(bill: Bill, instance, session: aiohttp.ClientSession):
    """
    Used to get the sponsors of a bill and add them to said bill.

    Parameters
    ----------
    bill: :class:`Bill`
        The bill instance.
    instance: :class:`UKParliament`
        The instance of the main class.
    session: :class:`session`
        The aiohttp session.
    """
    for stage in instance.get_bill_stages():
        if bill.get_current_stage_id() == stage.get_stage_id():
            bill.set_current_stage(stage)
            break

    url = f"{utils.URL_BILLS}/Bills/{bill.get_bill_id()}"
    async with session.get(url) as resp:
        if resp.status != 200:
            raise Exception(
                f"Couldn't fetch information for from url: '{resp.url}'/{bill.get_title()}."
                f" Status Code: {resp.status}"
            )
        bill_content = await resp.json()
        # print(json.dumps(bill_content, indent=4))
        sponsors = bill_content["sponsors"]

        pm_sponsors = []
        bill.set_long_title(bill_content["longTitle"])
        if sponsors is not None and len(sponsors) > 0:
            for sponsor in sponsors:
                sponsor_member = sponsor["member"]
                sponsor_member_name = sponsor_member["name"]
                sponsor_member_id = sponsor_member["memberId"]
                member = await instance.lazy_load_member(sponsor_member_id)

                if member is None:
                    raise Exception(
                        f"Couldn't find sponsor party member instance of sponsor {sponsor_member_name}"
                        f"/{sponsor_member_id}"
                    )

                pm_sponsors.append(member)
            bill.set_sponsors(pm_sponsors)


class SearchBillsSortOrder(utils.BetterEnum):
    TITLE_ASCENDING = "TitleAscending"
    TITLE_DESENCING = "TitleDescending"
    DATE_UPDATED_ASCENDING = "DateUpdatedAscending"
    DATE_UPDATED_DESENDING = "DateUpdatedDescending"


class SearchBillsBuilder:
    def __init__(self):
        self.bits = []

    @classmethod
    def builder(cls):
        return cls()

    def set_search_term(self, search_term: str):
        self.bits.append(f'SearchTerm={"%20".join(search_term.split(" "))}')
        return self

    def set_session(self, session: int):
        self.bits.append(f"Session={session}")
        return self

    def set_member_id(self, member_id: int):
        self.bits.append(f"MemberId={member_id}")
        return self

    def set_department_id(self, department_id: int):
        self.bits.append(f"DepartmentId={department_id}")
        return self

    def set_bill_stages(self, stages: list[BillStage]):
        self.bits.append(
            "&".join(
                list(map(lambda stage: f"BillStage={stage.get_stage_id()}", stages))
            )
        )
        return self

    def set_bill_type(self, btypes: list[BillType]):
        self.bits.append(
            "&".join(list(map(lambda btype: f"BillType={btype.get_id()}", btypes)))
        )
        return self

    def set_sort_order(
        self, order: SearchBillsSortOrder = SearchBillsSortOrder.DATE_UPDATED_DESENDING
    ):
        self.bits.append(f"SortOrder={order.value}")
        return self

    def set_current_house(self, house: str):
        self.bits.append(f"CurrentHouse={house}")
        return self

    def set_originating_house(self, house: str):
        self.bits.append(f"OriginatingHouse={house}")
        return self

    def build(self):
        if len(self.bits) > 0:
            return f"{utils.URL_BILLS}/Bills?{'&'.join(self.bits)}"
        return f"{utils.URL_BILLS}/Bills"
