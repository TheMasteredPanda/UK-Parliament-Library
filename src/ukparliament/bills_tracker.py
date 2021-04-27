from aiohttp.client import ClientSession
from bs4 import BeautifulSoup
import asyncio
from typing import Any, Union
from .utils import BetterEnum
from datetime import datetime, timedelta


class FeedUpdate:
    def __init__(self, feed_update_object):
        self._stage = (
            feed_update_object.attrs["p4:stage"]
            if "p4:stage" in feed_update_object.attrs
            else None
        )
        self._guid = feed_update_object.guid.text
        self._bill_id = self._guid.split("/")[-1]
        self._categories = [
            c.text.lower() for c in feed_update_object.find_all("category")
        ]
        self._title = feed_update_object.title.text
        self._description = feed_update_object.description.text.replace(
            "<description>", ""
        ).replace("</description>", "")
        updated_string_date = feed_update_object.find("a10:updated").text
        self._updated = (
            datetime.strptime(updated_string_date, "%Y-%m-%dT%H:%M:%SZ")
            if "Z" in updated_string_date
            else datetime.fromisoformat(updated_string_date)
        )

    def get_bill_id(self):
        return self._bill_id

    def get_stage(self):
        return self._stage

    def get_guid(self):
        return self._guid

    def get_title(self):
        return self._title

    def get_description(self):
        return self._description

    def get_update_date(self):
        return self._updated

    def get_categories(self):
        return self._categories


class PublicationUpdate:
    def __init__(self, publication_update):
        self._guid = publication_update.guid.text
        self._category = publication_update.category.text
        self._title = publication_update.title.text
        self._description = publication_update.description.text
        self._publication_date = datetime.strptime(
            publication_update.pubdate.text, "%a, %d %b %Y %H:%M:%S %z"
        )

    def get_guid(self):
        return self._guid

    def get_category(self):
        return self._category

    def get_title(self):
        return self._title

    def get_description(self):
        return self._description

    def get_publication(self):
        return self._publication_date


class BillsStorage:
    async def add_feed_update(self, bill_id: int, update: FeedUpdate):
        pass

    async def has_update_stored(self, bill_id: int, update: FeedUpdate):
        pass

    async def get_last_update(self, bill_id: int):
        pass

    async def add_publication_update(self, bill_id: int, update: PublicationUpdate):
        pass

    async def has_publication_update(self, bill_id: int, update: PublicationUpdate):
        pass


class Feed:
    """

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
    """

    def __init__(self, bill_url: str, session: ClientSession):

        self.bill_url = bill_url
        self.bill_id = self.bill_url.split("/")[-1]
        self.last_update = None
        self.last_publication_update = None
        self.rss_individual_url = (
            f"https://bills-api.parliament.uk/Rss/Bills/{self.bill_id}.rss"
        )
        self.session = session

    async def fetch_newest_publications(
        self,
        update_limit: int = 20,
    ):
        """
        Used to poll a bill for publication updates
        """
        async with self.session.get(self.rss_individual_url) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Couldn't fetch individual bill rss feed for bill {self.bill_id}. Status Code: {resp.status}"
                )

            soup = BeautifulSoup(await resp.text(), features="lxml")
            rss_last_update = datetime.strptime(
                soup.rss.channel.lastbuilddate.text, "%a, %d %b %Y %H:%M:%S %z"
            )

            if self.last_publication_update is not None:
                if self.last_publication_update >= rss_last_update:
                    return []

            results = []
            for item in soup.rss.channel.find_all("item"):
                update = PublicationUpdate(item)
                if (
                    self.last_publication_update is not None
                    and update.get_publication().timestamp()
                    < self.last_publication_update.timestamp()
                ):
                    break

                if len(results) >= update_limit:
                    break

                results.append(update)

            self.last_publication_update = rss_last_update
            return results

    async def process_poll_item(self, json_object):
        """
        Polls individual items from the main rss feed. Used primarily to get all the other information
        that should have been achievable through the individual bill rss feed but wasn't because heaven
        forbid anything could be _that_ simple.
        """
        update = FeedUpdate(json_object)
        if self.last_update is None:
            self.last_update = update.get_update_date()
            return update

        if self.last_update.timestamp() < update.get_update_date().timestamp():
            print(
                f"Feed {self.bill_id}: Last Update: {self.last_update} Date of FeedUpdate instance: "
                f"{update.get_update_date().timestamp()}"
            )
            self.last_update = update.get_update_date()
            return update
        return None

    def set_last_update(self, date):
        self.last_update = date

    def get_last_update(self):
        return self.last_update

    def get_id(self):
        return int(self.bill_id)

    def get_bill_url(self):
        return self.bill_url


class Conditions(BetterEnum):
    PUBLICATIONS = (0,)
    LORDS = (1,)
    COMMONS = (2,)
    GOV_BILL = (3,)
    PRI_BILL = (4,)
    ROYAL_ASSENT = (5,)
    ALL = 7


class TrackerListener:
    def __init__(self, func, conditions):
        self.func = func
        self.conditionals = conditions

    def meets_conditions(self, update: FeedUpdate):
        if Conditions.ALL in self.conditionals:
            return True

        if Conditions.LORDS in self.conditionals:
            if "lords" in update.get_categories():
                return True

        if Conditions.COMMONS in self.conditionals:
            if "commons" in update.get_categories():
                return True

        if Conditions.ROYAL_ASSENT in self.conditionals:
            if "royal assent" in (
                update.get_stage().lower() if update.get_stage() is not None else ""
            ):
                return True
        return False

    async def handle(self, feed: Feed, update: FeedUpdate):
        await self.func(feed, update)


class BillsTracker:
    def __init__(self, parliament, storage: BillsStorage, session: ClientSession):
        self._session = session
        self._parliament = parliament
        self._feeds: list[Feed] = []
        self._storage = storage
        self._listeners: list[TrackerListener] = []
        self._last_update: Union[datetime, None] = None

    # Loads previously tracked but not yet expired feeds as well as feeds that have not yet been tracked.
    def get_parliament(self):
        return self._parliament

    def get_storage(self):
        return self._storage

    async def start_event_loop(self):
        async def main():

            await asyncio.ensure_future(self.poll())
            await asyncio.sleep(30)
            await main()

        await main()

    async def _poll_task(self, feed: Feed, main_poll_object: Any = None):
        handler_tasks = []
        if self._listeners == 0:
            return
        update = await feed.process_poll_item(main_poll_object)
        if update is None:
            return
        is_stored = await self._storage.has_update_stored(feed.get_id(), update)
        if is_stored is True:
            return

        for listener in self._listeners:
            if listener.meets_conditions(update) is False:
                continue
            handler_tasks.append(listener.handle(feed, update))
            await self._storage.add_feed_update(feed.get_id(), update)

        if len(handler_tasks) > 0:
            await asyncio.gather(*handler_tasks)

    def get_feed(self, id: str):
        for feed in self._feeds:
            if feed.get_id() == id:
                return feed
        return None

    def register(self, func, conditionals: list[Conditions] = []):
        self._listeners.append(TrackerListener(func, conditionals))

    # Polls the currently tracked feeds, creates new feeds that have not yet been tracked, and expires feeds
    # That have not been updated for at least two months.

    async def poll(self):
        tasks = []
        async with self._session.get(
            "https://bills-api.parliament.uk/Rss/allbills.rss"
        ) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Couldn't fetch rss feed for all bills. Status code: {resp.status}"
                )
            soup = BeautifulSoup(await resp.text(), features="lxml")

            rss_last_update = datetime.strptime(
                soup.rss.channel.lastbuilddate.text, "%a, %d %b %Y %H:%M:%S %z"
            )
            items = reversed(soup.rss.channel.find_all("item"))

            if self._last_update is not None:
                if self._last_update.timestamp() >= rss_last_update.timestamp():
                    return

            self._last_update = rss_last_update

            for item in items:
                bill_id = item.guid.text.split("/")[-1]  # type: ignore
                feed = None
                if item.guid.text in [f.get_bill_url() for f in self._feeds]:
                    feed = self.get_feed(bill_id)
                else:
                    feed = Feed(item.guid.text, self._session)
                    self._feeds.append(feed)

                if feed is None:
                    continue
                tasks.append(self._poll_task(feed, item))

        await asyncio.gather(*tasks)
        self.bills_first_polling = False

    def get_feeds(self):
        return self._feeds


class PublicationsTracker:
    def __init__(
        self,
        tracker: BillsTracker,
        *,
        pffl: int = 10,
    ):
        self._tracker = tracker
        self._last_polled = None
        self._load_per_feed_fetch_limit = pffl
        self._first_index = True
        self.listeners = []

    def register(self, listener_func):
        self.listeners.append(listener_func)

    def get_last_polled(self):
        return self._last_polled

    async def start_event_loop(self):
        async def main():
            await asyncio.ensure_future(self.poll())
            await asyncio.sleep(30)
            await main()

        await main()

    async def poll(self):
        async def _task(update: PublicationUpdate, func):
            await func(update)

        fetch_tasks = []
        tasks = []

        for feed in self._tracker.get_feeds():

            async def _fetch_task(feed: Feed):
                updates = (
                    await feed.fetch_newest_publications(
                        self._load_per_feed_fetch_limit
                    )
                    if self._first_index
                    else await feed.fetch_newest_publications()
                )

                if len(updates) > 0:
                    for update in updates:
                        if await self._tracker.get_storage().has_publication_update(
                            feed.get_id(), update
                        ):
                            continue

                        await self._tracker.get_storage().add_publication_update(
                            feed.get_id(), update
                        )
                        for listener in self.listeners:
                            tasks.append(_task(update, listener))

            fetch_tasks.append(_fetch_task(feed))

        self._last_polled = datetime.now()
        await asyncio.gather(*fetch_tasks)
        await asyncio.gather(*tasks)
        if self._first_index:
            self._first_index = False


async def dual_event_loop(b_tracker: BillsTracker, p_tracker: PublicationsTracker):
    async def main():
        await b_tracker.poll()
        await p_tracker.poll()
        await asyncio.sleep(30)
        await main()

    await main()
