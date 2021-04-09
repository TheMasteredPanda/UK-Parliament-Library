import json
import requests

URL = 'http://eldaddp.azurewebsites.net'

def load_data(session: requests.Session, url: str, page_size: int = -1):
    """
    Iterates through results that are pageinated and stiches all the results together.

    session: python modules Session instance for the UKParliament instance.
    url: The URL of the first (page 0) page.
    """

    def iterate(session: requests.Session, url: str, results: list):
        response = session.get(url)
        if response.status_code != 200:
            raise Exception(f"Couldn't continue to iterate over pages of data as {page_url} responded with error code {response.status_code}")
        content = json.loads(response.content)
        if len(content['result']['items']) > 0: results.extend(content['result']['items'])

        if 'next' not in content['result']:
            return results
        else:
            if page_size == -1:
                return iterate(session, content['result']['next'], results)
            else:
                return iterate(session, f"{content['result']['next']}&_pageSize={page_size}", results)

    return iterate(session, url, [])
