
from structures.constituencies import Constituency


class PartyMember():
    def __init__(self, json_party_member):
        self.member_resource_url = json_party_member['_about']
        self.middle_name = json_party_member['additionalName']['_value'] if 'additionalName' in json_party_member else ''
        self.first_name = json_party_member['familyName']['_value']
        self.last_name = json_party_member['givenName']['_value']
        self.gender = json_party_member['gender']['_value']
        self.website = json_party_member['homePage'] if 'homePage' in json_party_member else ''
        self.label = json_party_member['label']['_value'] #TODO: What is this label for? 
        self.party = json_party_member['party']['_value']
        self.twitter = json_party_member['twitter']['_value'] if 'twitter' in json_party_member else '' #TODO: This might have to become a list if more social media platforms are linked

    @classmethod
    def create(cls, json_party_member):
        return cls(json_party_member)

    def get_full_name(self, middle_name: bool = False):
        return f'{self.first_name} {self.last_name}'

    def get_gender(self):
        return self.gender

    def get_website(self):
        return self.website

    def get_party(self):
        return self.party

    def get_constituency(self) -> Constituency:
        return self.constituency

    def _set_constituency(self, constituency):
        self.constituency = constituency

    def get_twitter(self):
        return self.twitter

    def _get_member_resource(self):
        return self.member_resource_url

class Party(): #TODO
    def __init__(self):
        pass

class Chamber(): #TODO
    def __init__(self):
        pass


