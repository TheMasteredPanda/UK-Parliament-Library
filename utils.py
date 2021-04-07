import json
import requests

URL = 'https://lda.data.parliament.uk'

def load_data(session: requests.Session, url: str):
    """
    Iterates through results that are pageinated and stiches all the results together.

    session: python modules Session instance for the UKParliament instance.
    url: The URL of the first (page 0) page.
    """
    results = []

    def _iterate(page_url: str):
        response = session.get(page_url)
        if response.status_code != 200:
            raise Exception(f"Couldn't continue to iterate over pages of data as {page_url} responded with error code {response.status_code}")
        content = json.loads(response.content)
        results.extend(content['result']['items'])
        if 'next' in content['result']:
            _iterate(content['result']['next'])

    _iterate(url)
    return results
