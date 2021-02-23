from abc import abstractmethod
from typing import ClassVar, List

import discord
from discord.ext import commands
from tortoise import Model, fields


class PreferenceScope(Model):
    scope_name: ClassVar[str] = 'Unnamed'
    preference_names: ClassVar[List[str]] = []

    class Meta:
        abstract = True

    @classmethod
    @abstractmethod
    async def get_from_context(cls, ctx: commands.Context):
        raise NotImplementedError


class Guild(PreferenceScope):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)  # Doesn't need to stay up to date. Just for reference.
    timezone_preference = fields.CharField(max_length=31, default='')
    language_preference = fields.CharField(max_length=15, default='')
    prefix_preference = fields.CharField(max_length=15, default='')

    scope_name = 'Guild'
    preference_names = ['timezone', 'language', 'prefix']

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        if not ctx.guild:
            return None
        return (await cls.update_or_create(id=ctx.guild.id, name=ctx.guild.name))[0]

    def __str__(self):
        return f'{self.name} ({self.id})'


class Channel(PreferenceScope):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)  # Doesn't need to stay up to date. Just for reference.
    timezone_preference = fields.CharField(max_length=31, default='')
    language_preference = fields.CharField(max_length=15, default='')

    scope_name = 'Channel'
    preference_names = ['timezone', 'language']

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        return (await cls.update_or_create(id=ctx.channel.id, name=ctx.channel.name))[0]

    def __str__(self):
        return f'{self.name} ({self.id})'


class User(PreferenceScope):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)  # Doesn't need to stay up to date. Just for reference.
    timezone_preference = fields.CharField(max_length=31, default='')
    language_preference = fields.CharField(max_length=15, default='')

    scope_name = 'User'
    preference_names = ['timezone', 'language']

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        return (await cls.update_or_create(id=ctx.author.id, name=f'{ctx.author.name}#{ctx.author.discriminator}'))[0]

    def __str__(self):
        return f'{self.name} ({self.id})'


TORTOISE_ORM = {
    'connections': {'default': 'sqlite://db.sqlite3'},
    'apps': {
        'models': {
            'models': ['miyu_bot.bot.models', 'aerich.models'],
            'default_connection': 'default',
        },
    },
}
