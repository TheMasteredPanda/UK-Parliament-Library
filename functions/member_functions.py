from structures.elections import ElectionResult
from structures.members import PartyMember, Party
import requests
import json
import utils
class MemberFunctions():
    def __init__(self):
        self.members = []

    '''
    - Use election results to determine the currently sitting members.
    '''
    def _index(self, session: requests.Session, results: list[ElectionResult], c_functions):
        for result_item in results:
            response = requests.get(f'{utils.URL}/members.json?constituency={result_item._get_constituency_resource()}')
            if response.status_code != 200: raise Exception(f"Couldn't fetch member by representing constituency. Status Code: {response.status_code}")
            content = json.loads(response.content)
            member = PartyMember(content['result']['items'][0])
            member._set_constituency(c_functions.get_constituency_by_id(result_item.get_constituency_id()))
            self.members.append(member)

    def get_members(self):
        return self.members
