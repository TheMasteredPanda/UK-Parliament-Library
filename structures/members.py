
class PartyMember():
    def __init__(self, json_party_member):
        self.member_resource_url = json_party_member['_about']
        self.middle_name = json_party_member['additionalName']['_value']
        self.first_name = json_party_member['familyName']['_value']
        self.last_name = json_party_member['givenName']['_value']
        self.gender = json_party_member['gender']['_value']
        self.website = json_party_member['homePage']
        self.label = json_party_member['label']['_value'] #TODO: What is this label for? 
        self.party = json_party_member['party']['_value']
        self.twitter = json_party_member['twiter']['_value'] #TODO: This might have to become a list if more social media platforms are linked
        self.constituency = None

    def get_full_name(self, middle_name: bool = False):
        return f'{self.first_name} {self.last_name}'

    def get_gender(self):
        return self.gender

    def get_website(self):
        return self.website

    def get_party(self):
        return self.party

    def get_constituency(self):
        return self.constituency

    def _set_constituency(self, constituency):
        self.constituency = constituency

    def get_twitter(self):
        return self.twitter

class Party():
    def __init__(self):
        pass

class Chamber():
    def __init__(self):
        pass


