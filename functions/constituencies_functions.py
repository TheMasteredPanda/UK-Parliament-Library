import utils
import json
import requests
from ukparliament import UKParliament
from structures.constituencies import Constituency
from structures.elections import ElectionResult

class ConstituenciesFunctions():
    def __init__(self):
        """
        Class containing functions relevent to the constituencies module.
        """
        self.constituencies: list[Constituency] = []

    def _index(self, session: requests.Session, results: list[ElectionResult], use_list: bool = False):
        """
        Fetches all 650 currently active constituencies through the relevant endpoint or all the constituencies
        in the election results list, if stated.

        session: request Session used in the main instance.
        results: the election results list.
        use_list: whether to get the currently used constituencies via the relevant endpoint or use the
        election_results list to populate the list of constituencies. The latter might be relevant to use
        if the election results pre-date that of the creation of the currently used constituencies.
        """
        self.constituencies.clear() # Empties 

        def _index_from_list():
            for result_item in results:
                response = requests.get(f'{utils.URL}/constituencies/{result_item.get_constituency_id()}')
                content =  json.loads(response.content)
                c_item = Constituency(content['result']['primaryTopic'])
                c_item._set_election_result(result_item)
                self.constituencies.append(c_item)


        request = session.get(f'{utils.URL}/constituencies?_sort=endedDate&_pageSize=650')
        if request.status_code != 200: raise Exception(f"Couldn't fetch used constituencies. Code: {request.status_code}")
        c_results = json.loads(request.content)['result']['items']
        for item in c_results: 
            c_item = Constituency(item)
            
            for result_item in results:
                if result_item._get_constituency_resource() == c_item._get_constituency_resource():
                    c_item._set_election_result(result_item)


    def get_constituencies(self):
        return self.constituencies

    def get_constituency_by_id(self, constituency_id: str):
        for constituency in self.constituencies:
            if constituency.get_id() == constituency_id:
                return constituency

    #Government Statical Service Code assigned to the constituency.
    def get_constitueny_by_gss(self, gss_code: str):
        for constituency in self.constituencies:
            if constituency.get_gss_code() == gss_code:
                return constituency
