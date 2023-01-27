import logging
from typing import Dict, Type

from discord.ext import commands

from miyu_bot.bot import models
import miyu_bot.bot.bot
from miyu_bot.bot.models import PreferenceScope, all_preferences


class Preferences(commands.Cog):
    bot: "miyu_bot.bot.bot.MiyuBot"

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        from miyu_bot.commands.master_filter.localization_manager import (
            LocalizationManager,
        )

        self.l10n = LocalizationManager(self.bot.fluent_loader, "preferences.ftl")

    @commands.hybrid_command(name="setpref", description="", help="")
    async def setpref(self, ctx: commands.Context, scope: str, name: str, value: str):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f"Invalid scope.")
            return
        if name not in scope.preferences:
            await ctx.send(f"Invalid preference.")
            return
        preference = scope.preferences[name]
        if not (
            await ctx.bot.is_owner(ctx.author)
            or (scope.has_permissions(ctx) and not preference.is_privileged)
        ):
            await ctx.send(f"Insufficient permissions.")
            return
        if error_message := preference.validate_or_get_error_message(value):
            await ctx.send(f"Invalid value: {error_message}")
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f"Scope not available in current channel.")
            return
        entry.set_preference(name, value)
        await entry.save()
        await ctx.send(f"Preference updated.")

    @commands.hybrid_command(name="getpref", description="", help="")
    async def getpref(self, ctx: commands.Context, scope: str, name: str = ""):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f"Invalid scope.")
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f"Scope not available in current channel.")
            return
        if name:
            if name not in scope.preferences:
                await ctx.send(f"Invalid preference.")
                return
            await ctx.send(
                str(getattr(entry, scope.preferences[name].attribute_name) or None)
            )
        else:
            await ctx.send(
                "\n".join(
                    f"{name}: {getattr(entry, pref.attribute_name)}"
                    for name, pref in scope.preferences.items()
                    if not pref.is_privileged
                )
            )

    @commands.hybrid_command(name="clearpref", description="", help="")
    async def clearpref(self, ctx: commands.Context, scope: str, name: str = ""):
        scope = preference_scope_aliases.get(scope)
        if not scope:
            await ctx.send(f"Invalid scope.")
            return
        if name not in scope.preferences:
            await ctx.send(f"Invalid preference.")
            return
        preference = scope.preferences[name]
        if not (
            await ctx.bot.is_owner(ctx.author)
            or (scope.has_permissions(ctx) and not preference.is_privileged)
        ):
            await ctx.send(f"Insufficient permissions.")
            return
        entry = await scope.get_from_context(ctx)
        if not entry:
            await ctx.send(f"Scope not available in current channel.")
            return
        entry.clear_preference(name)
        await entry.save()
        await ctx.send(f"Successfully cleared preference.")


preference_scope_aliases: Dict[str, Type[PreferenceScope]] = {
    "user": models.User,
    "self": models.User,
    "channel": models.Channel,
    "server": models.Guild,
    "guild": models.Guild,
}


async def get_preferences(ctx: commands.Context, toggle_user_prefs: bool = False):
    sources = []
    if guild_prefs := ctx.guild and await models.Guild.get_or_none(id=ctx.guild.id):
        sources.append(guild_prefs)
    if channel_prefs := await models.Channel.get_or_none(id=ctx.channel.id):
        sources.append(channel_prefs)
    if user_prefs := await models.User.get_or_none(id=ctx.author.id):
        if not toggle_user_prefs:
            sources.append(user_prefs)

    preference_values = {}
    for source in sources:
        for k, v in source.preferences.items():
            if source.preference_set(k):
                preference_values[v.name] = source.get_preference(k)
    for v in all_preferences.values():
        if v.name not in preference_values:
            preference_values[v.name] = v.default_value
    return preference_values


async def setup(bot):
    await bot.add_cog(Preferences(bot))
