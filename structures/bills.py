
class Bill():
    def __init__(self, json_object):
        value_object = json_object['value']
        self.bill_id = value_object['billID']
        self.title = value_object['shortTitle']
        self.current_house = value_object['currentHouse']
        self.originating_house = value_object['originatingHouse']
        self.last_update = value_object['lastUpdate']
        self.defeated = value_object['isDefeated']
        self.withdrawn = value_object['billWithdrawn']
        self.bill_type = value_object['billType']['id']
        self.bill_type_name = value_object['billType']['name']
        self.bill_order = value_object['billType']['order']
        self.sessions = value_object['sessions']
        self.current_stage = value_object['currentStage']
