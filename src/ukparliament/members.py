import asyncio
import aiohttp
from .structures.members import PartyMember, ElectionResult, VotingEntry
from cachetools import TTLCache
from threading import Lock
from . import utils


async def er_task(er_member: PartyMember, session: aiohttp.ClientSession):
    """
    A task used to fetch election results for each member.

    Parameters
    ----------
    er_member: :class:`PartyMember`
        The member who represents a constituency (MP).
    session: :class:`ClientSession`
        A aiohttp client session.

    Returns
    -------
    A list of :class:`ElectionResult` instances for the :class:`PartyMember` specified.
    """
    async with session.get(
        f"{utils.URL_MEMBERS}/Location/Constituency/{er_member._get_membership_from_id()}"
        "/ElectionResults"
    ) as elections_resp:
        if elections_resp.status != 200:
            raise Exception(
                f"Couldn't fetch election results for MP Borough {er_member.get_addressed_name()}/"
                f"{er_member.get_id()}. Status Code: {elections_resp.status}"
            )

        elections_obj = await elections_resp.json()

        async def inner_task(
            session: aiohttp.ClientSession, borough_id: int, election_id: int
        ):
            async with session.get(
                f"{utils.URL_MEMBERS}/Location/Constituency/{borough_id}/ElectionResult/"
                f"{election_id}"
            ) as election_resp:
                if election_resp.status != 200:
                    raise Exception(
                        f"Couldn't fetch election result {election_id}. "
                        f"Status Code: {election_resp.status}"
                    )
                content = await election_resp.json()
                result = ElectionResult(content["value"])
                return result

        election_tasks = []

        for election_json_obj in elections_obj["value"]:
            election_tasks.append(
                inner_task(
                    session,
                    er_member._get_membership_from_id(),
                    election_json_obj["electionId"],
                )
            )
        elections = await asyncio.gather(*election_tasks)
        return elections


async def vh_task(
    vi_member: PartyMember, session: aiohttp.ClientSession, cache: TTLCache, lock: Lock
):
    """
    A task used to fetch the voting history for each member.

    Parameters
    ----------
    vi_member: :class:`PartyMember`
        A party member instance, used to fetch the voting history for said member.
    session: :class:`ClientSession`
        A aiohttp client session.
    cache: :class:`TTLCache`
        The voting history cache, used to fetch history entries in the near future.
    lock: :class:`Lock`
        The cache lock for the voting history cache.
    """
    url = f"{utils.URL_MEMBERS}/Members/{vi_member.get_id()}/Voting?house="
    f'{"Commons" if vi_member.is_mp() is True else "Lords"}'
    items = await utils.load_data(url, session)

    voting_list = []

    for item in items:
        entry = VotingEntry(item)
        voting_list.append(entry)

    with lock:
        cache[vi_member.get_id()] = voting_list
