from d4dj_utils.master.event_master import EventMaster, EventState
from discord.ext import commands

from main import masters


def get_latest_event(ctx: commands.Context) -> EventMaster:
    """Returns the oldest event that has not ended or the newest event otherwise."""
    try:
        # NY event overlapped with previous event
        return min((v for v in masters.events.values(ctx) if v.state() == EventState.Open),
                   key=lambda e: e.start_datetime)
    except ValueError:
        try:
            return min((v for v in masters.events.values(ctx) if v.state() < EventState.Ended),
                       key=lambda e: e.start_datetime)
        except ValueError:
            return max(masters.events.values(ctx), key=lambda v: v.start_datetime)

