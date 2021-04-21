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
    def __init__(self, rss_url, storage: Storage):
        self.storage = storage
        self.bill_id = rss_url.split('/')[-1].replace('.rss', '')
        self.entries = []
        self.last_update_date: Union[datetime.datetime, None] = None
        self.published_date: Union[datetime.datetime, None] = None
        self.url = rss_url

    async def load(self):
        self.entries = await self.storage.get_feed_update_ids(self.bill_id)

    async def poll(self, session: ClientSession, testing: bool = False):
        async with session.get(self.url) as rss_resp:
            if rss_resp.status != 200:
                raise Exception(f"Couldn't fetch rss feed of {self.url}. Status Code: {rss_resp.status}")

            text = await rss_resp.text()
            parsed_text = feedparser.parse(text)
            rss_feed_update = dateparser.parse(parsed_text['feed']['updated']) #type: ignore
            if self.last_update_date is not None:
                if self.last_update_date.timestamp() >= rss_feed_update.timestamp():
                    return
            else:
                self.last_update_date = rss_feed_update

            if self.published_date is None:
                self.published_date = dateparser.parse(parsed_text['feed']['published']) #type: ignore


            updates = []
            last_update_entry = None

            for entry in parsed_text['entries']:
                entry_date = dateparser.parse(entry['published']) #type: ignore
                if entry_date > self.last_update_date or testing is True: #type: ignore
                    updates.append(FeedUpdate(entry))
                    last_update_entry = entry_date
                else:
                    await self.storage.store_update_ids(self.bill_id, updates)
                    self.entries = await self.storage.get_feed_update_ids(self.bill_id)
                    self.last_update_date = entry_date
                return updates

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



    async def handle(self, feed: Feed, update: FeedUpdate):
        await self.func(feed, update)

class Tracker:
    def __init__(self, parliament, storage: Storage, event_loop: AbstractEventLoop = None):
        self.parliament = parliament
        self.feeds: list[Feed] = []
        self.storage = storage
        self.listeners: list[TrackerListener] = []
        self.last_update: Union[datetime.datetime, None] = None
        self.loop = asyncio.new_event_loop() if event_loop is None else event_loop
        asyncio.set_event_loop(self.loop)

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
            updates = await feed.poll(session, testing)
            if updates is None or len(updates) == 0: return
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
            async with session.get('https://bills-api.parliament.uk/Rss/allbills.rss') as resp:
                if resp.status != 200:
                    raise Exception(f"Couldn't fetch rss feed for all bills. Status code: {resp.status}")

                parsed_text = feedparser.parse(await resp.text())
                rss_last_update = dateparser.parse(parsed_text['feed']['updated']) #type: ignore
                if self.last_update is not None:
                    if self.last_update.timestamp() >= rss_last_update.timestamp():
                        print("Dates equal. No need to additionally poll.")
                        return
                else:
                    self.last_update = rss_last_update

                    print(f'Parsing {len(parsed_text["items"])} items')
                    for item in parsed_text['items']:
                        bill_id = item['id'].split('/')[-1] #type: ignore
                        if self.is_feed_already(bill_id):
                            continue
                        self.feeds.append(Feed(f'https://bills-api.parliament.uk/Rss/Bills/{bill_id}.rss', storage=self.storage))

        tasks = []
        for feed in self.feeds:
            tasks.append(self._poll_task(feed, testing))
        await asyncio.gather(*tasks)
