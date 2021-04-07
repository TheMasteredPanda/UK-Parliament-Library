from structures.elections import ElectionResult
import requests
import json

class MemberFunctions():
    '''
    - Use election results to determine the currently sitting members.
    '''
    def _index(self, session: requests.Session, results: list[ElectionResult]):
        pass


    def fetch_all_members(self):
        response = requests.get('https://lda.data.parliament.uk/members.json')
        return json.loads(response.content)
