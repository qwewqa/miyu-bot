import enum
import logging
from collections import defaultdict
from typing import Dict, Type

import pytz
from discord.ext import commands

from miyu_bot.bot import models
from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.models import PreferenceScope


class Preferences(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name='setpref',
                      description='',
                      help='')
    async def setpref(self, ctx: commands.Context, scope: str, name: str, value: str):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f'Invalid scope "{scope.scope_name}".')
            return
        if scope != models.User and not (await ctx.bot.is_owner(ctx.author) or
                                         ctx.author.guild_permissions.administrator):
            await ctx.send(f'Altering preferences for scope "{scope.scope_name}" requires administrator permissions.')
            return
        if name not in scope.preference_names:
            await ctx.send(f'Invalid preference "{name}" for scope "{scope.scope_name}".')
            return
        value = preference_transformers[name](value)
        if not preference_validators[name](value):
            await ctx.send(f'Invalid value "{value}" for preference "{name}".')
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.scope_name}" not available in current channel.')
            return
        original = getattr(entry, f'{name}_preference')
        setattr(entry, f'{name}_preference', value)
        await entry.save()
        await ctx.send(f'Successfully changed preference "{name}" '
                       f'for scope "{scope.scope_name}" from "{original}" to "{value}".')

    @commands.command(name='getpref',
                      description='',
                      help='')
    async def getpref(self, ctx: commands.Context, scope: str, name: str = ''):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f'Invalid scope "{scope.scope_name}".')
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.scope_name}" not available in current channel.')
            return
        if name:
            if name not in scope.preference_names:
                await ctx.send(f'Invalid preference "{name}" for scope "{scope.scope_name}".')
                return
            await ctx.send(str(getattr(entry, f'{name}_preference') or None))
        else:
            names = scope.preference_names
            await ctx.send('\n'.join(f'{name}: {getattr(entry, f"{name}_preference")}' for name in names))


preference_scope_aliases: Dict[str, Type[PreferenceScope]] = {
    'user': models.User,
    'self': models.User,
    'channel': models.Channel,
    'server': models.Guild,
    'guild': models.Guild,
}

default_preferences = {
    'timezone': 'etc/utc',
    'language': 'en',
    'prefix': '!',
}

lowercase_timezones = {tz.lower() for tz in pytz.all_timezones_set}

preference_validators = {
    'timezone': lambda v: v in lowercase_timezones or not v,
    'language': lambda v: False,
    'prefix': lambda v: len(v) <= 15 or not v,
}

preference_transformers = defaultdict(**{
    'timezone': lambda v: v.lower(),
}, default_factory=lambda: lambda v: v)

preference_names = default_preferences.keys()


async def get_preferences(ctx: commands.Context, use_user: bool):
    sources = []
    if user := use_user and await models.User.get_or_none(id=ctx.author.id):
        sources.append(user)
    if channel := await models.Channel.get_or_none(id=ctx.channel.id):
        sources.append(channel)
    if guild := ctx.guild and await models.Guild.get_or_none(id=ctx.guild.id):
        sources.append(guild)

    preferences = {}
    for name in preference_names:
        preferences[name] = next(
            (v for v in (getattr(s, f'{name}_preference') for s in sources if name in s.preference_names) if v),
            default_preferences[name])
    return preferences


def setup(bot):
    bot.add_cog(Preferences(bot))
