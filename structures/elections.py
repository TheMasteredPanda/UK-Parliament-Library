import utils
import aiohttp
import json

class ElectionResult():
    def __init__(self, result_json, election_result_json):
        """
        Serialized the data relevant to this result. 

        session: the request session used for the UKParliament instance.
        result_json: The result of a json entry fetched from the elections module.
        """
        self.result_resource_url = result_json['_about']
        self.result_id = result_json['_about'].split('/')[-1]
        self.constituency_resource_url = result_json['constituency']['_about']
        self.election_resource_url = result_json['election']['_about']
        self.electorate = result_json['electorate']
        self.winners_majority = result_json['majority']
        self.result = result_json['resultOfElection']
        self.turnout = result_json['turnout']
        self.candidates = []
        self.election_label = result_json['election']['label']['_value']
        for candidate in election_result_json['result']['primaryTopic']['candidate']:
            self.candidates.append({'name': candidate['fullName']['_value'], 'votes': candidate['numberOfVotes'], 'order': candidate['order'], 'party': candidate['party']['_value']})

        self.winner = list(filter(lambda c: c['order'] == 1, self.candidates))[0]

    @classmethod
    async def create(cls, session: aiohttp.ClientSession, result_json):
        async with session.get(f'{utils.URL}/electionresults/{result_json["_about"].split("/")[-1]}.json') as resp: # Gets the winner and the rest of the candidates. This includes candidate voting results and the order for the candidates from the winner to the least voted candidate.

            if resp.status != 200:
                raise Exception(f"Couldn't fetch election results for result entry {result_json['_about']}/{result_json['constituency']['label']['_value']}")
            content = await resp.json()
            return cls(result_json, content)

    def get_election_label(self):
        return self.election_label

    def _get_constituency_resource(self):
        return self.constituency_resource_url

    def _get_election_resource(self):
        return self.election_resource_url

    def _get_result_resource(self):
        return self.result_resource_url

    def get_result_id(self):
        return self.result_id

    def get_electorate(self):
        return self.electorate # The number of people registered to vote in this constituency

    def get_turnout(self):
        return self.turnout # The amount of registered voters who vote.

    def get_constituency_id(self):
        return self.constituency_resource_url.split('/')[-1]

    def get_winners_majority(self):
        return self.winners_majority # The majority difference between the winner and the second best candidate.

    def get_candidates(self):
        """
        A list of dictionaries holding candidate information. Each dictionary is structured like so:
        {
            name: Name of the candidate
            votes: The amount of votes that candidate got.
            order: The order they came in (determined by how many votes they get)
            party: The string id of the party the candidate is a member of.
        }
        """
        return self.candidates

    def get_winner(self):
        return self.winner #The winner is a dictionary entry from the candidates list. Here solely for conveneience.

    def get_result(self):
        return self.result #The result of this election.
