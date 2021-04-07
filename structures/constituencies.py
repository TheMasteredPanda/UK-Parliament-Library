
class Constituency():
    def __init__(self, constituency_json):
        """
        Serializes constituency data.

        constituency_json: The deserialized data.
        """
        self.constituency_type = constituency_json['constituencyType']
        self.constituency_resource_url = constituency_json['_about']
        self.gss_code = constituency_json['gssCode']
        self.label  = constituency_json['label']['_value']
        self.os_name = constituency_json['osName'] #What does 'osName' represent?
        self.represented_by = None
        self.result = None
        self.established_date = constituency_json['startedDate']['_value']

    def get_type(self):
        return self.constituency_type

    #Government Statistical Service Code assigned to the constituency
    def get_gss_code(self):
        return self.gss_code

    def get_label(self):
        return self.label

    def get_mp(self):
        return self.represented_by

    def _set_mp(self, mp):
        self.represented_by = mp

    def _set_election_result(self, result):
        self.result = result

    def get_election_result(self):
        return self.result

    def get_established_date(self):
        return self.established_date

    def get_constituency_id(self):
        return self.constituency_resource_url.split('/')[-1]

    def _get_constituency_resource(self):
        return self.constituency_resource_url
