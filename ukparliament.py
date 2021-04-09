import json
import utils
import requests
from functions.member_functions import MemberFunctions
from functions.constituencies_functions import ConstituenciesFunctions
from structures.elections import ElectionResult

__author__ = 'TheMasteredPanda'
__status__ = 'Development'
__version__ = '1.0'

'''
---------------------------------------------------------
A Python Interface for the UK Parliament Rest API. 

The central point of contact is the UKParliament class,
each instance can index data from one election onwards,
until the date of the next election - this is to not
index unnecessary data. 
---------------------------------------------------------
'''

class UKParliament():
    def __init__(self, election_identifier: str, use_list: bool = False, modules: list = ['bills']):
        """
        Returns a UKParliament instance with serialized data from the UK Parliament
        Rest API. Each module specified will be accessible through this point of contact.

        election_identifier: a string parameter that can either be an election id, that
        is the id used in the UK Parliament API to identify elections, or the date the
        election was held in yyyy-mm-dd format, so in the 2019 General Election this parameter would be
        2019-12-12

        modules: the list of modules to load. These modules refer to the function modules that contain
        functions that interface with data fetched from a section of the api. Each module is named after 
        the api section in the DataSets page site. By default members, and constituencies are loaded.

        The following are the names of the modules and it's relation to the modules on the api:
            - bills: Bills
            - commons_answered_questions: Commons Answered Questions
            - commons_divisions: Commons Divisions
            - commons_oral_question_times: Commons Oral Question Times
            - commons_oral_questions: Commons Oral Questions
            - commons_written_questions: Commons Written Questions
            - constituencies: Constituences (loaded by default)
            - early_day_motions: Early Day Motions
            - election_results: Election Results (loaded by default, partially)
            - elections: Elections (loaded by default, partially)
            - lords_attendances: Lords Attendances
            - lords_bill_amendments: Lords Bill Amendments
            - lords_divisions: Lords Divisions
            - lords_written_questions: Lords Written Questions
            - members: Members (loaded by default)
            - papers_laid: Papers Laid (loaded by default)
            - parliamentary_questions_answered: Parliamentary Questions Answered
            - publication_logs: Publication Logs
            - research_briefings: Research Briefings
            - sessions: Sessions
            - thesaurus: Thesaurus
            - e_petitions: e-Petitions
        """
        self.session = requests.Session() # Using session for connection pooling capabilities. 
        election_id = self._check_validity_of_identifier(election_identifier)
        if election_id is False: raise Exception(f'Provided election identifier is not valid.')
        self.member_functions = MemberFunctions()
        self.constituencies_functions = ConstituenciesFunctions()
        self.election_results = [] # A list of serialized election results.
        self.load(str(election_id), use_list)
        self.election_id = election_id

    def members(self):
        return self.member_functions

    def load(self, election_id: str, use_list: bool):
        """
        Loads all the modules.

        election_id: The id of the election either provided or derived from the 
        _check_validity_of_identifer function. This is used to determine what
        information should be loaded into this instance. 

        Once the election results of this election have been fetched both the
        constituencies module and members module are loaded in that order. After
        that every other module is loaded.
        """
        results = utils.load_data(self.session, f'{utils.URL}/electionresults.json?electionId={election_id}&_pageSize=100', 100)

        for item in results:
            self.election_results.append(ElectionResult(self.session, item))

        print(len(self.election_results))
        self.constituencies_functions._index(self.session, self.election_results, )
        self.member_functions._index(self.session, self.election_results, self.constituencies_functions)

    def _check_validity_of_identifier(self, election_identifier: str):
        """
        Checks the validity of the election identifier by checking if the entry exists on the api.

        election_identifier: A date string formatted as yyyy-mm-dd or the id of the election entry as
        seen on the UK Parliament Rest API.

        returns the election id if the election identifier is valid, else a false boolean.
        """
        if election_identifier is None or election_identifier == '': return False
        if len(election_identifier.split('-')) != 3 and election_identifier.isnumeric() is False: return False
        response = None

        if len(election_identifier.split('-')) == 3:
            response = self.session.get(f'{utils.URL}/elections.json?date={election_identifier}')
        else:
            respone = self.session.get(f'{utils.URL}/elections/{election_identifier}')

        if response.status_code != 200:
            raise Exception("Couldn't check the validity of the election identifer")

        content = json.loads(response.content)
        if int(content['result']['totalResults']) == 0: return False
        return election_identifier if election_identifier.isnumeric() else content['result']['items'][0]['_about'].split('/')[-1]

parliament = UKParliament('2019-12-12')
