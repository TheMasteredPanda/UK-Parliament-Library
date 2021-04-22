import asyncio
from asyncio.events import AbstractEventLoop
import time
import aiohttp
import dateparser
import datetime
from typing import Any, Union
from aiohttp.client import ClientSession
import feedparser
import schedule
from .utils import BetterEnum

class Storage:
    async def get_feed_update_ids(self, bill_id: int) -> list:
        return []

    async def store_update_ids(self, bill_id: int, updates: list[str]):
        pass

    async def update_stored(self, guid: str) -> bool:
        return False

    async def get_feeds(self) -> list[Any]:
        '''
        Returns a list of feeds that were being tracked to be tracked
        once more.
        '''
        return []

    async def expire_feed(self, guid: str):
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
        The date the feed was last updated. Derived from the feed metadata of the
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
    def __init__(self, rss_url, storage: Storage, new: bool = False):
        self.storage = storage
        self.bill_id = rss_url.split('/')[-1].replace('.rss', '')
        self.entries = []
        self.last_update_date: Union[datetime.datetime, None] = None
        self.published_date: Union[datetime.datetime, None] = None
        self.url = rss_url
        self.new = new

    async def load(self):
        self.entries = await self.storage.get_feed_update_ids(self.bill_id)

    def get_bill_id(self):
        return self.bill_id

    def get_last_update_date(self):
        return self.last_update_date

    async def poll(self, session: ClientSession, testing: bool = False, debug_log: bool = False):
        if debug_log: print(f"Feed {self.url} being polled.")
        async with session.get(self.url) as rss_resp:
            if rss_resp.status != 200:
                raise Exception(f"Couldn't fetch rss feed of {self.url}. Status Code: {rss_resp.status}")
            
            if debug_log: print(f"Feed {self.url}: Fetched rss feed.")

            text = await rss_resp.text()
            parsed_text = feedparser.parse(text)
            rss_feed_update = dateparser.parse(parsed_text['feed']['updated']) #type: ignore

            if self.last_update_date is not None:
                if self.last_update_date.timestamp() == rss_feed_update.timestamp():
                    if debug_log: print(f"Feed {self.url}: Feed has not been updated since last poll. No need to poll aditionally.")
                    return
            else:
                self.last_update_date = rss_feed_update

            if debug_log: print(f"Feed {self.url}: Feed has been updated since last poll. Polling additionally")

            if self.published_date is None:
                if debug_log: print(f"Feed {self.url}: Published date not yet set. Setting published date.")
                self.published_date = dateparser.parse(parsed_text['feed']['published']) #type: ignore


            updates: list[FeedUpdate] = []
            last_update_entry = None

            if debug_log: print(f"Feed {self.url}: Iterating through {len(parsed_text['entries'])} updates. Will only index updates timestamped after {self.last_update_date.isoformat()}.")

            for entry in parsed_text['entries']:
                entry_date = dateparser.parse(entry['published']) #type: ignore
                if entry_date.timestamp() > self.last_update_date.timestamp() or testing is True or self.new is True: #type: ignore
                    if self.new and debug_log is True: print(f"Feed {self.url}: Fetched first update due to new feed.")
                    updates.append(FeedUpdate(entry))
                    last_update_entry = entry_date
                    self.new = False
                    
            if len(updates) > 0:
                if debug_log: print(f"Feed {self.url}: found {len(updates)} updates. Storing update ids and returning updates.")
                await self.storage.store_update_ids(self.bill_id, [update.get_id() for update in updates])
                self.entries = await self.storage.get_feed_update_ids(self.bill_id)
                self.last_update_date = last_update_entry
                return updates
            if debug_log: print(f"Feed {self.url}: No updates found.")
            return []

    def get_id(self):
        return self.bill_id

    def get_last_date(self):
        return self.last_update_date

    def get_url(self):
        return self.url

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
                    return True


        if Conditions.LORDS_SITTING in self.conditionals:
            if 'house of lords' in update.get_summary().lower():
                if 'sitting' in [tag['term'].lower() for tag in update.get_tags()]:
                    return True
                return False
            else:
                return False

        if Conditions.COMMITEE_SITTING in self.conditionals:
            if 'house of commons' in update.get_summary().lower():
                if 'sitting' in [tag['term'].lower() for tag in update.get_tags()]:
                    return True
                return False
            else:
                return False
        return True



    async def handle(self, feed: Feed, update: FeedUpdate):
        await self.func(feed, update)

class Tracker:
    def __init__(self, parliament, storage: Storage, event_loop: AbstractEventLoop = None, debug_log: bool = False):
        self.parliament = parliament
        self.feeds: list[Feed] = []
        self.storage = storage
        self.listeners: list[TrackerListener] = []
        self.last_update: Union[datetime.datetime, None] = None
        self.loop = asyncio.new_event_loop() if event_loop is None else event_loop
        asyncio.set_event_loop(self.loop)
        self.debug_log = debug_log

    #Loads previously tracked but not yet expired feeds as well as feeds that have not yet been tracked.
    async def start_event_loop(self, testing: bool = False):
        async def main():
            asyncio.ensure_future(self._poll(testing))
            await asyncio.sleep(30)
            await main()

        await main()
    
    def get_event_loop(self):
        return self.loop

    async def _load(self):
        '''
        Loads feeds that were once being tracked from the storage medium
        into feed instances.
        '''
        print('Loading feeds')
        self.feeds = await self.storage.get_feeds()


    async def _poll_task(self, feed: Feed, testing: bool = False):
        handler_tasks = []

        async with aiohttp.ClientSession() as session:
            updates = await feed.poll(session, testing, self.debug_log)
            if updates is None or len(updates) == 0: 
                if self.debug_log: print(f"No updates returned for feed {feed.get_url()}")
                return
            if self.debug_log: print(f"Updates found for feed {feed.get_url()}")
            for update in updates:
                for listener in self.listeners:
                    if listener.meets_conditions(update) is False:
                        continue
                    handler_tasks.append(listener.handle(feed, update))
            if len(handler_tasks) > 0:
                asyncio.gather(*handler_tasks)

    def is_feed_already(self, id: str):
        for feed in self.feeds:
            if feed.get_id() == id:
                return True
        return False
            
    def register(self, func, conditionals: list[Conditions] = []):
        self.listeners.append(TrackerListener(func, conditionals))

    #Polls the currently tracked feeds, creates new feeds that have not yet been tracked, and expires feeds
    #That have not been updated for at least two months. 
    async def _poll(self, testing: bool = False):
        async with aiohttp.ClientSession() as session:
            if self.debug_log: print('Fetching rss feed')
            async with session.get('https://bills-api.parliament.uk/Rss/allbills.rss') as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch rss feed for all bills. Status code: {resp.status}")
                if self.debug_log: print('Fetched rss feed')
                parsed_text = feedparser.parse(await resp.text())
                rss_last_update = dateparser.parse(parsed_text['feed']['updated']) #type: ignore
                if self.last_update is not None:
                    if self.last_update.timestamp() >= rss_last_update.timestamp():
                        if self.debug_log: print(f"Dates equal. No need to additionally poll. {rss_last_update}")
                        return

                self.last_update = rss_last_update

                if self.debug_log: print(f"Parent poll. Last Update: {self.last_update} RSS Last Update: {rss_last_update}")
                if self.debug_log: print(f'Parsing {len(parsed_text["items"])} items')
                for item in parsed_text['items']:
                    bill_id = item['id'].split('/')[-1] #type: ignore
                    if self.is_feed_already(bill_id):
                        continue
                    self.feeds.append(Feed(f'https://bills-api.parliament.uk/Rss/Bills/{bill_id}.rss', storage=self.storage, new=True))
                    

        tasks = []
        for feed in self.feeds:
            tasks.append(self._poll_task(feed, testing))
        await asyncio.gather(*tasks)
