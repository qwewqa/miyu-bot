import enum
import logging
from typing import Dict, Type

import pytz
from discord.ext import commands
from tortoise import Model

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
            await ctx.send(f'Invalid scope "{scope.__name__}".')
            return
        if scope != models.User and not (ctx.author == self.bot.owner_id or ctx.author.guild_permissions.administrator):
            await ctx.send(f'Altering preferences for scope "{scope.__name__}" requires administrator permissions.')
        if name not in preferences_sets_by_scope[scope]:
            await ctx.send(f'Invalid preference "{name}" for scope "{scope.__name__}".')
            return
        if not preference_validators[name](value):
            await ctx.send(f'Invalid value "{value}" for preference "{name}".')
            return
        entry: PreferenceScope = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.__name__}" not available in current channel.')
            return
        setattr(entry, f'{name}_preference', value)
        await entry.save()
        await ctx.send(f'Successfully updated preference.')

    @commands.command(name='getpref',
                      description='',
                      help='')
    async def getpref(self, ctx: commands.Context, scope: str, name: str = ''):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f'Invalid scope "{scope.__name__}".')
            return
        entry: PreferenceScope = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f'Scope "{scope.__name__}" not available in current channel.')
            return
        if name:
            if name not in preferences_sets_by_scope[scope]:
                await ctx.send(f'Invalid preference "{name}" for scope "{scope.__name__}".')
                return
            await ctx.send(str(getattr(entry, f'{name}_preference') or None))
        else:
            names = preferences_by_scope[scope]
            await ctx.send('\n'.join(f'{name}: {getattr(entry, f"{name}_preference")}' for name in names))


preference_scope_aliases: Dict[str, Type[PreferenceScope]] = {
    'user': models.User,
    'self': models.User,
    'channel': models.Channel,
    'server': models.Guild,
    'guild': models.Guild,
}

default_preferences = {
    'timezone': 'Etc/UTC',
    'language': 'en'
}

preference_validators = {
    'timezone': lambda v: v in pytz.all_timezones_set,
    'language': lambda v: False
}

preference_names = default_preferences.keys()

preference_scopes = {
    'timezone': {models.User, models.Channel, models.Guild},
    'language': {models.User, models.Channel, models.Guild}
}

preferences_sets_by_scope = {scope: {pref for pref, scopes in preference_scopes.items() if scope in scopes}
                             for scope in [models.User, models.Channel, models.Guild]}

preferences_by_scope = {scope: [pref for pref, scopes in preference_scopes.items() if scope in scopes]
                        for scope in [models.User, models.Channel, models.Guild]}


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
        preferences[name] = next((v for v in (getattr(s, f'{name}_preference') for s in sources) if v),
                                 default_preferences[name])
    return preferences


def setup(bot):
    bot.add_cog(Preferences(bot))
