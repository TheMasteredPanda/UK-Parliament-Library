import datetime
from typing import Union
import dateparser
from structures.members import PartyMember

class BillStage():
    def __init__(self, json_object):
        self.stage_id = json_object['id']
        self.name = json_object['name']
        self.order = json_object['sortOrder']
        self.category_stage = json_object['stageCategory']
        self.prominent_order = json_object['prominentSortOrder']
        self.house = json_object['house']

    def get_stage_id(self) -> int:
        return self.stage_id

    def get_name(self) -> str:
        return self.name

    def get_order(self) -> str:
        return self.order

    def get_category_stage(self) -> str:
        return self.category_stage

    def get_prominent_order(self) -> int:
        return self.prominent_order

    def get_house(self):
        return self.house

class BillType():
    def __init__(self, json_object):
        self.bill_type_id = json_object['id']
        self.category = json_object['category']
        self.name = json_object['name']
        self.description = json_object['description']
        self.order = json_object['order']

    def get_id(self) -> int:
        return self.bill_type_id

    def get_category(self) -> str:
        return self.category

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def get_order(self) -> int:
        return self.order

class Bill():
    def __init__(self, json_object):
        value_object = json_object['value']
        self.bill_id = value_object['billID']
        self.title = value_object['shortTitle']
        self.current_house = value_object['currentHouse']
        self.originating_house = value_object['originatingHouse']
        self.last_update = dateparser.parse(value_object['lastUpdate'])
        self.defeated = value_object['isDefeated']
        self.withdrawn = value_object['billWithdrawn'] if value_object['billWithdrawn'] is not None else False
        self._bill_type_id = value_object['billType']['id']
        self.sessions = value_object['sessions']
        self.curent_stage_id = value_object['currentStage']['stageId']
        self.current_stage_sitting = value_object['currentStage']['stageSitting']
        self.current_stage = None
        self.royal_assent = value_object['hasRoyalAssent']
        self.act = value_object['isAct']
        self.bill_type = None
        self.sponsors: list[PartyMember] = []
        self.long_title = None

    def _set_long_title(self, long_title: str):
        self.long_title = long_title

    def _set_sponsors(self, sponsors: list[PartyMember]):
        self.sponsors.extend(sponsors)

    def _set_bill_type(self, btype):
        self.bill_type = btype

    def get_long_title(self) -> Union[str, None]:
        return self.long_title

    def get_sponsors(self) -> list[PartyMember]:
        return self.sponsors

    def has_royal_assent(self) -> bool:
        return self.royal_assent

    def is_act(self) -> bool:
        return self.act

    def get_bill_id(self) -> int:
        return self.bill_id

    def get_title(self) -> str:
        return self.title

    def get_current_house(self) -> str:
        return self.current_house
    
    def get_originating_house(self) -> str:
        return self.originating_house

    def get_last_update(self) -> Union[datetime.datetime, None]:
        return self.last_update

    def was_defeated(self) -> bool:
        return self.defeated

    def was_withdrawan(self) -> bool:
        return self.withdrawn

    def get_bill_type(self) -> Union[BillType, None]:
        return self.bill_type

    def get_sessions_accomodated(self) -> list:
        return self.sessions

    def _set_current_stage(self, current_stage):
        self.current_stage = current_stage

    def get_current_stage(self) -> Union[BillStage, None]:
        return self.current_stage


