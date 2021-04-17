from .structures.bills import Bill, BillStage, BillType, PartyMember
import aiohttp
from . import utils


async def division_task(instance, m_id, member_list: list[PartyMember]):
    member = instance.get_member_by_id(m_id)
    if member is None: member = await instance._lazy_load_member(m_id)
    if member is None:
        raise Exception(f"Couldn't find member {m_id}")
    member_list.append(member)

async def _meta_bill_task(bill: Bill, instance, session: aiohttp.ClientSession = None):
    for stage in instance.get_bill_stages():
        if bill._get_current_stage_id() == stage.get_stage_id():
            bill._set_current_stage(stage)
            break

    url = f"{utils.URL_BILLS}/Bills/{bill.get_bill_id()}"
    async with session.get(url) if session is not None else aiohttp.ClientSession().get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Couldn't fetch information for from url: '{resp.url}'/{bill.get_title()}. Status Code: {resp.status}")
            bill_content = await resp.json()
            sponsors = bill_content['value']['sponsors']

            pm_sponsors = []
            bill._set_long_title(bill_content['value']['longTitle'])
            if sponsors is not None and len(sponsors) > 0:
                for json_sponsor in sponsors:
                    member = instance.get_member_by_id(json_sponsor['memberId'])
                    if member is None:
                        member = await instance._lazy_load_member(json_sponsor['memberId'])

                        if member is None:
                            raise Exception(f"Couldn't find sponsor party member instance of sponsor {json_sponsor['name']}/{json_sponsor['memberId']}")
                    pm_sponsors.append(member)
                bill._set_sponsors(pm_sponsors)

class SearchBillsSortOrder(utils.BetterEnum):
    TITLE_ASCENDING = 'TitleAscending'
    TITLE_DESENCING = 'TitleDesending'
    DATE_UPDATED_ASCENDING = 'DateUpdatedAscending'
    DATE_UPDATED_DESENDING = 'DateUpdatedDescending'

class SearchBillsBuilder():
    def __init__(self):
        self.bits = []

    @classmethod
    def builder(cls):
        return cls()
    
    def set_search_term(self, search_term: str):
        self.bits.append(f'SearchTerm={"%20".join(search_term.split(" "))}')
        return self

    def set_session(self, session: int):
        self.bits.append(f'Session={session}')
        return self

    def set_member_id(self, member_id: int):
        self.bits.append(f'MemberId={member_id}')
        return self

    def set_department_id(self, department_id: int):
        self.bits.append(f'DepartmentId={department_id}')
        return self

    def set_bill_stages(self, stages: list[BillStage]):
        self.bits.append('&'.join(list(map(lambda stage: f'BillStage={stage.get_stage_id()}', stages))))
        return self

    def set_bill_type(self, btypes: list[BillType]):
        self.bits.append('&'.join(list(map(lambda btype: f'BillType={btype.get_id()}', btypes))))
        return self

    def set_sort_order(self, order: SearchBillsSortOrder = SearchBillsSortOrder.DATE_UPDATED_DESENDING):
        self.bits.append(f'SortOrder={order.value}')
        return self

    def set_current_house(self, house: str):
        self.bits.append(f'CurrentHouse={house}')
        return self

    def set_originating_house(self, house: str):
        self.bits.append(f'OriginatingHouse={house}')
        return self

    def build(self):
        if len(self.bits) > 0:
            return f"{utils.URL_BILLS}/Bills?{'&'.join(self.bits)}"
        return f"{utils.URL_BILLS}/Bills"

