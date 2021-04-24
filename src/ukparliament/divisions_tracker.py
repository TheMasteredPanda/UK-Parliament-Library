
import asyncio
from typing import Union
import aiohttp
from ukparliament.bills import SearchBillsBuilder
from ukparliament.utils import BetterEnum
from .structures.bills import Bill, LordsDivision, CommonsDivision

class DivisionStorage:
    async def add_division(self, division: Union[LordsDivision, CommonsDivision]):
        '''
        Used to store division information that is not related to a bill. 
        '''
        pass

    async def add_bill_division(self, bill_id: int, division: Union[LordsDivision, CommonsDivision]):
        '''
        Used to store division information that is relataed to a bill.
        '''
        pass

    async def division_stored(self, division: Union[LordsDivision, CommonsDivision]):
        '''
        Used to check if a division that is not related to a bill has been stored. 
        '''
        pass

    async def bill_division_stored(self, bill_id: int, division: Union[LordsDivision, CommonsDivision]):
        '''
        Used to check if a division that is related to a bill has been stored.
        '''
        pass

    async def get_bill_divisions(self, bill_id: int):
        '''
        Used to fetch all the divions relating to a bill.
        '''
        pass

class DivisionsTracker:
    def __init__(self, parliament, storage: DivisionStorage):
        self.parliament = parliament
        self.lords_listeners = []
        self.commons_listeners = []
        self.last_update = None
        self.storage = storage
        pass
    
    def register(self, func, commons_listener: bool = True):
        if commons_listener:
            self.commons_listeners.append(func)
        else:
            self.lords_listeners.append(func)
    
    async def start_event_loop(self):
        async def main():
            #asyncio.ensure_future(self._poll_commons())
            asyncio.ensure_future(self._poll_lords())
            await asyncio.sleep(30)
            await main()
        await main()


    async def _division_task(self, division: Union[LordsDivision, CommonsDivision]):
        has_been_stored = await self.storage.division_stored(division)
        if has_been_stored: return
        title = division.get_division_title() 
        bill = None
        if 'Bill' in title:
            bill_section = title.split("Bill")[0] + "Bill"
            bills = await self.parliament.search_bills(url=SearchBillsBuilder.builder().set_search_term(bill_section).build())
            if len(bills) > 0:
                bill = bills[0]

        if bill is not None:
            has_been_stored_b = await self.storage.bill_division_stored(bill.get_bill_id(), division)
            if has_been_stored_b: return


        if bill is not None:
            await self.storage.add_bill_division(bill.get_bill_id(), division)
        else:
            await self.storage.add_division(division)

        listener_tasks = []

        for listener in self.lords_listeners if isinstance(division, LordsDivision) else self.commons_listeners:
            listener_tasks.append(listener(division, bill))

        await asyncio.gather(*listener_tasks)

    async def _poll_commons(self):
        divisions = await self.parliament.search_for_commons_divisions(result_limit=10)

        tasks = []
        for division in divisions:
            tasks.append(self._division_task(division))
        await asyncio.gather(*tasks)

    async def _poll_lords(self):
        divisions = await self.parliament.search_for_lords_divisions(result_limit=10)
        print(f"Got {len(divisions)} lords divisions.")

        tasks = []
        for division in divisions:
            tasks.append(self._division_task(division))
        await asyncio.gather(*tasks)