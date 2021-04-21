import asyncio
import aiohttp
import dateparser
import datetime
from typing import Any, Union
from aiohttp.client import ClientSession
import feedparser
import schedule
from .ukparliament import UKParliament
from .utils import BetterEnum

class Storage:
    def get_feed_update_ids(self, bill_id: int) -> dict:
        return {}

    def store_updates(self, updates: list):
        pass

    def update_stored(self, guid: str) -> bool:
        return False

    def get_feeds(self) -> list[Any]:
        '''
        Returns a list of feeds that were being tracked to be tracked
        once more.
        '''
        return []

    def expire_feed(self, guid: str):
        pass

class FeedUpdate:
    def __init__(self, feed_update_object):
        self.id = feed_update_object['id']
        self.guid_is_link = feed_update_object['guidislink']
        self.link = feed_update_object['link']
        self.links = feed_update_object['links']
        self.tags = feed_update_object['tags']
        self.title = feed_update_object['title']
        self.summary = feed_update_object['summary']
        self.published = dateparser.parse(feed_update_object['published'])
        self.stage = feed_update_object['p4_stage'] if 'p4_stage' in feed_update_object else None

    def get_id(self):
        return self.id

    def is_guid_link(self):
        return self.guid_is_link

    def get_link(self):
        return self.link

    def get_links(self):
        return self.links

    def get_tags(self):
        return self.tags

    def get_title(self):
        return self.title

    def get_summary(self):
        return self.summary

    def get_published(self):
        return self.published

    def get_stage(self):
        return self.stage

class Feed:
    '''     feed 


    A feed is a object representation of an rss feed of a single bill.
    This feed will handle the poll request for that specific rss feed.

    Variables
    ----------
    entries:
        A list of rss update ids associated with this bill. The feed will not
        load all but the updates that have not been stored yet.
    last_update_date:
        The date the feed was last updated. Derived from the headers of the
        rss feed.
    published_date:
        The date the bill was first published.

    Parameters
    ----------
    rss_url:
        The rss url for an individual bill.
    storage:
        The storage medium in which the update guids will be stored for 
        each bill.
    '''
    def __init__(self, rss_url, storage: Storage):
        self.storage = storage
        self.bill_id = rss_url.split('/')[-1].replace('.rss', '')
        self.entries = storage.get_feed_update_ids(self.bill_id)
        self.last_update_date = self.get_latest_update()
        self.published_date = None
        self.url = rss_url

    async def poll(self, session: ClientSession):
        async with session.head(self.url) as resp:
            if resp.status != 200:
                raise Exception(f"Couldn't fetch headers of {self.url}. Status Code: {resp.status}")
            header_date = dateparser.parse(resp.headers['Date'])
            if self.last_update_date > header_date:
                return []
            async with session.get(self.url) as rss_resp:
                if rss_resp.status != 200:
                    raise Exception(f"Couldn't fetch rss feed of {self.url}. Status Code: {rss_resp.status}")
                text = await rss_resp.text()
                parsed_text = feedparser.parse(text)
                if self.published_date is None:
                    self.published_date = dateparser.parse(parsed_text['feed']['pubDate']) #type: ignore

                updates = []

                for entry in parsed_text['entries']:
                    entry_date = dateparser.parse(entry['published']) #type: ignore
                    
                    if entry_date > self.last_update_date:
                        updates.append(FeedUpdate(entry))
                    else:
                        self.storage.store_updates(updates)
                        self.entries = self.storage.get_feed_update_ids(self.bill_id)
                        self.last_update_date = self.get_latest_update()
                        return updates


    def get_latest_update(self):
        key = None

        for entry_key in self.entries.keys():
            if key is None:
                key = entry_key
                continue

            if self.entries[key]['date'] < self.entries[entry_key]:
                key = entry_key

        return self.entries[key]

class Conditions(BetterEnum):
    PUBLICATIONS = 0,
    LORDS_SITTING = 1,
    COMMONS_SITTING = 2,
    COMMITEE_SITTING = 3
    
class TrackerListener:
    def __init__(self, func, conditions):
        self.func = func
        self.conditionals = conditions

    def meets_conditions(self, update: FeedUpdate):
            if Conditions.PUBLICATIONS in self.conditionals:
                for tag in update.get_tags():
                    if tag['term'].lower() == 'publication':
                        return False

            if Conditions.LORDS_SITTING in self.conditionals:
                if ['house of lords', 'committee'] in update.get_summary().lower() and Conditions.COMMITEE_SITTING:
                    return False

                if ['house of lords'] in update.get_summary().lower():
                    if 'sitting' not in update.get_title().lower():
                        return False
                else:
                     return False

            if Conditions.COMMITEE_SITTING in self.conditionals:
                if ['house of commons', 'committee'] in update.get_summary().lower() and Conditions.COMMITEE_SITTING:
                    return False

                if ['house of commons'] in update.get_summary().lower():
                    if 'sitting' not in update.get_title().lower():
                        return False
                else:
                    return False
            return True



    async def handle(self, update: FeedUpdate):
        await self.func(update)

class Tracker:
    def __init__(self, parliament: UKParliament, storage: Storage):
        self.parliament = parliament
        self.feeds = []
        self.storage = storage
        self.listeners: list[TrackerListener] = []
        self.last_update: Union[datetime.datetime, None] = None

    #Loads previously tracked but not yet expired feeds as well as feeds that have not yet been tracked.
    async def _load(self):
        feeds = []

        if self.storage is not None:

            pass

    async def _poll_task(self, feed: Feed):
        handler_tasks = []

        async with aiohttp.ClientSession() as session:
            updates = await feed.poll(session)
            if updates is None or len(updates) == 0: return
            for update in updates:
                for listener in self.listeners:
                    if listener.meets_conditions(update) is False:
                        continue
                    handler_tasks.append(listener.handle(update))
            if len(handler_tasks) > 0:
                asyncio.run(*handler_tasks)
            
    #Polls the currently tracked feeds, creates new feeds that have not yet been tracked, and expires feeds
    #That have not been updated for at least two months. 
    async def _poll(self):

        async with aiohttp.ClientSession() as session:
            async with session.head('https://bills-api.parliament.uk/Rss/allbills.rss') as h_resp:
                if h_resp.status != 200:
                    raise Exception(f"Couldn't fetch rss feed for all bills. Status code: {h_resp.status}")

                header_date = dateparser.parse(h_resp.headers['Date'])
                if self.last_update is None or header_date > self.last_update:
                    async with session.get('https://bills-api.parliament.uk/Rss/allbills.rss') as resp:
                        if resp.status != 200:
                            raise Exception(f"Couldn't fetch rss feed for all bills. Status code: {resp.status}")

                        parsed_text = feedparser.parse(await resp.text())

                        for item in parsed_text['item']:
                            #TODO: find feed it is already being tracked
                            #TODO: if feed is not found, create new feed
                            #TODO: poll feed.
                            pass
