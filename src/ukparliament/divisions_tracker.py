import asyncio
from typing import Union
from ukparliament.bills import SearchBillsBuilder, SearchBillsSortOrder
from .structures.bills import LordsDivision, CommonsDivision


class DivisionStorage:
    """
    An interface used by :class:`DivisionsTracker` to allow for multiple storage mediums to be used with this feature.

    This is used primarily to not reannounce already announced divisions.
    """

    async def add_division(self, division: Union[LordsDivision, CommonsDivision]):
        """
        Add a division not associated to a bill to the storage medium.

        Parameters
        ----------
        division: :class:`Union[LordsDivision, CommonsDivision]`
            The division to store.
        """
        pass

    async def add_bill_division(
        self, bill_id: int, division: Union[LordsDivision, CommonsDivision]
    ):
        """
        Add a division associated to a bill to the storage medium.

        Parameters
        ----------
        bill_id: :class:`int`
            The id of a bill associated with a division.
        division: :class:`Union[LordsDivision, CommonsDivision]`
            The division to store.
        """
        pass

    async def division_stored(
        self, division: Union[LordsDivision, CommonsDivision]
    ) -> bool:
        """
        Check if a division not associated to a bill is stored.

        Parameters
        ----------
        division: :class:`Union[LordsDivision, CommonsDivision]`
            The division to check for.

        Returns
        -------
        A :class:`bool` True if stored, else False.
        """
        return False

    async def bill_division_stored(
        self, bill_id: int, division: Union[LordsDivision, CommonsDivision]
    ) -> bool:
        """
        Check if a division that is associated with a bill is stored.

        Parameters
        ----------
        bill_id: :class:`int`
            The id of the bill associated with a division.
        division: :class:`Union[LordsDivision, CommonsDivision]`
            The division to check for.

        Returns
        -------
        A :class:`bool` True if stored, else False.
        """

        return False

    async def get_bill_divisions(self, bill_id: int) -> list[object]:
        """
        Fetches entries from the storage medium containing unique data points form :class:`LordsDivision`
        and :class:`CommonsDivision` instances.

        Parameters
        ----------
        bill_id: :class:`int`
            The bill id associated to some divisions.

        Returns
        -------
        A :class:`list` of json objects with unique data points associated to a bill id.
        """
        return []


class DivisionsTracker:
    def __init__(self, parliament, storage: DivisionStorage):
        """
        DivisionsTracker tracks divisions from both the House of Lords and the House of Commons by
        repeatedly searching for the most recently added divisions on the REST API every 30 seconds.

        New division are then injected into listeners registered with the tracker.

        Parameters
        ----------
        parliament: :class:`UKParliament`
            An instance of the main class, used to fetch the most recently added divisions.
        storage: :class:`DivisionStorage`
            The storage interface the tracker will use.
        """
        self.parliament = parliament
        self.lords_listeners = []
        self.commons_listeners = []
        self.last_update = None
        self.storage = storage
        pass

    def register(self, func, commons_listener: bool = True):
        """
        Register a listener with the tracker.

        Parameters
        ----------
        func: :class:`func`
            The function called when a new division has been identified.
        commons_listener: :class:`bool`
            A boolean that determines if the listener is for the House of Commons (true)
            of the House of Lords (false)
        """
        if commons_listener:
            self.commons_listeners.append(func)
        else:
            self.lords_listeners.append(func)

    async def start_event_loop(self):
        """
        Starts the event loop.
        """

        async def main():
            asyncio.ensure_future(self.poll_commons())
            asyncio.ensure_future(self.poll_lords())
            await asyncio.sleep(30)
            await main()

        await main()

    async def division_task(self, division_id: int, lords_division: bool = False):
        """
        This task is used to process the new division and get the :class:`LordsDivision` or
        :class:`CommonsDivision` relevant to that division_id as well as a :class:`Bill` if
        the division is attached to a bill.

        Parameters
        ----------
        division_id: :class:`int`
            The id of the division.
        lords_division: :class:`bool`
            A boolean that determines if the new division is a Lords or Commons division.
        """
        division = (
            await self.parliament.get_lords_division(division_id)
            if lords_division
            else await self.parliament.get_commons_division(division_id)
        )
        has_been_stored = await self.storage.division_stored(division)
        if has_been_stored:
            return
        title = division.get_division_title()
        bill = None
        if "Bill" in title:
            bill_section = title.split("Bill")[0] + "Bill"
            bills = await self.parliament.search_bills(
                url=SearchBillsBuilder.builder()
                .set_search_term(bill_section)
                .set_sort_order(SearchBillsSortOrder.TITLE_DESENCING)
                .build()
            )
            if len(bills) > 0:
                for b in bills:
                    if b.get_title().startswith(bill_section):
                        bill = b

        if bill is not None:
            has_been_stored_b = await self.storage.bill_division_stored(
                bill.get_bill_id(), division
            )
            if has_been_stored_b:
                return

        if bill is not None:
            await self.storage.add_bill_division(bill.get_bill_id(), division)
        else:
            await self.storage.add_division(division)

        listener_tasks = []

        for listener in (
            self.lords_listeners
            if isinstance(division, LordsDivision)
            else self.commons_listeners
        ):
            listener_tasks.append(listener(division, bill))

        await asyncio.gather(*listener_tasks)

    async def poll_commons(self):
        """
        A main event loop function, used to poll commons divisions.
        """
        divisions = await self.parliament.search_for_commons_divisions(result_limit=10)

        tasks = []
        for division in divisions:
            tasks.append(self.division_task(division.get_id(), False))
        await asyncio.gather(*tasks)

    async def poll_lords(self):
        """
        A main event loop function, used to poll lords divisions.
        """
        divisions: list[
            LordsDivision
        ] = await self.parliament.search_for_lords_divisions(result_limit=10)
        divisions.reverse()

        tasks = []
        for division in divisions:
            tasks.append(self.division_task(division.get_id(), True))
        await asyncio.gather(*tasks)
