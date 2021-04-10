import time
import asyncio
import json
import utils
import aiohttp
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


TODO:
    - Session Functions -   To get the dates of all Parliamentary sessions.
                            Once we have those I can then sort the bills
                            by session to get the bills laid after the 
                            election date/id specified.
    - Bills Functions  -    Using the session data I can index the bills
                            relevant to the general election id/date in-
                            putted.
    - Commons Divisions Functions -
                            To get data on the vote of the bill in a stage,
                            hopefully I do not need to index this.
'''

class UKParliament():
    def __init__(self):
        self.member_functions = MemberFunctions()
        self.constituencies_functions = ConstituenciesFunctions()
        self.election_results = [] # A list of serialized election results.

    def members(self):
        return self.member_functions

    async def load(self, election_identifer: str, modules: list[str] = ['bills']):
        """
        Loads all the modules.

        election_id: The id of the election either provided or derived from the 
        _check_validity_of_identifer function. This is used to determine what
        information should be loaded into this instance. 

        Once the election results of this election have been fetched both the
        constituencies module and members module are loaded in that order. After
        that every other module is loaded.

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
        async with aiohttp.ClientSession() as session: 
            election_id = await self._check_validity_of_identifier(session, election_identifer)
            self.election_id = election_id
            results = await utils.load_data(f'{utils.URL}/electionresults.json?electionId={election_id}&_pageSize=100', session)
            tasks = []

            for item in results:
                tasks.append(ElectionResult.create(session, item))

            self.election_results.extend(await asyncio.gather(*tasks))
            await self.constituencies_functions._index(session, self.election_results)
            await self.member_functions._index(session, self.election_results, self.constituencies_functions)

    async def _check_validity_of_identifier(self, session: aiohttp.ClientSession, election_identifier: str):
        """
        Checks the validity of the election identifier by checking if the entry exists on the api.

        election_identifier: A date string formatted as yyyy-mm-dd or the id of the election entry as
        seen on the UK Parliament Rest API.

        returns the election id if the election identifier is valid, else a false boolean.
        """
        if election_identifier is None or election_identifier == '': return False
        if len(election_identifier.split('-')) != 3 and election_identifier.isnumeric() is False: return False
        url = None

        if len(election_identifier.split('-')) == 3:
            url = f'{utils.URL}/elections.json?date={election_identifier}'
        else:
            url = f'{utils.URL}/elections/{election_identifier}'

        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception("Couldn't check the validity of the election identifer")

            content = await resp.json()
            if int(content['result']['totalResults']) == 0: return False
            return election_identifier if election_identifier.isnumeric() else content['result']['items'][0]['_about'].split('/')[-1]

    def get_election_id(self):
        return self.election_id

parliament = UKParliament()
start = time.time()
asyncio.run(parliament.load('2019-12-12'))
end = time.time()
print(end - start)
print(parliament.get_election_id())
