import copy
from abc import abstractmethod
from typing import ClassVar, Callable, Any, Optional, Dict, Type, Tuple

import pytz
from discord.ext import commands
from tortoise import Model, fields
from tortoise.models import ModelMeta


class Preference:
    name: str
    attribute_name: str
    scope: 'PreferenceScope'

    def __init__(self,
                 name: str,
                 field: fields.Field,
                 default_value: Any,
                 unset_value: Any,
                 validator: Callable[[str], Optional[str]] = lambda _: None,
                 transformer: Callable[[str], Any] = lambda v: v):
        self.name = name
        self.field = field
        self.default_value = default_value
        self.unset_value = unset_value
        self._validator = validator
        self._transformer = transformer

    def validate(self, value: str) -> Optional[str]:
        return self._validator(value)

    def transform(self, value: str) -> Any:
        return self._transformer(value)


all_preferences = {}


class PreferenceScopeMeta(ModelMeta):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        # Not going to properly support overriding preferences in base classes.
        # Could be added if necessary.
        preferences = {}
        for k, v in attrs.items():
            if isinstance(v, Preference):
                if v.name in all_preferences:
                    if v != all_preferences[v.name]:
                        raise AttributeError(f'Encountered multiple preferences globally with name {k}.')
                else:
                    all_preferences[v.name] = v
                v = copy.deepcopy(v)
                v.attribute_name = k
                if k in preferences:
                    raise AttributeError(f'Encountered multiple preferences in a model with name {k}.')
                preferences[k] = v
        for k, v in preferences.items():
            attrs[k] = v.field
        attrs['preferences'] = preferences
        return super().__new__(mcs, name, bases, attrs)


class PreferenceScope(Model, metaclass=PreferenceScopeMeta):
    scope_name: ClassVar[str] = 'Unnamed'
    preferences: ClassVar[Dict[str, 'Preference']]

    class Meta:
        abstract = True

    @classmethod
    @abstractmethod
    async def get_from_context(cls, ctx: commands.Context):
        raise NotImplementedError

    def get_preference(self, name):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        value = getattr(self, preference.attribute_name)
        if value == preference.unset_value:
            value = preference.default_value
        return value

    def set_preference(self, name, value):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        if error_message := preference.validate(value):
            raise ValueError(error_message)
        setattr(self, preference.attribute_name, preference.transform(value))

    def clear_preference(self, name):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        setattr(self, preference.attribute_name, preference.unset_value)


lowercase_tzs = {tz.lower() for tz in pytz.all_timezones_set}

timezone_pref = Preference('timezone',
                           fields.CharField(max_length=31, default=''),
                           default_value='etc/utc',
                           unset_value='',
                           validator=lambda tz: None if tz.lower() in lowercase_tzs else 'Invalid timezone.',
                           transformer=lambda tz: tz.lower())
language_pref = Preference('language',
                           fields.CharField(max_length=15, default=''),
                           default_value='en',
                           unset_value='',
                           validator=lambda lang: 'Translations are not supported yet.')
prefix_pref = Preference('prefix',
                         fields.CharField(max_length=63, default=''),
                         default_value='!',
                         unset_value='',
                         validator=lambda prefix: None if len(prefix) <= 15 else 'Prefix is too long.')


class Guild(PreferenceScope):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)  # Doesn't need to stay up to date. Just for reference.

    scope_name = 'Guild'
    timezone = timezone_pref
    language = language_pref
    prefix = prefix_pref

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

    scope_name = 'Channel'
    timezone = timezone_pref
    language = language_pref

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        return (await cls.update_or_create(id=ctx.channel.id, name=ctx.channel.name))[0]

    def __str__(self):
        return f'{self.name} ({self.id})'


class User(PreferenceScope):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)  # Doesn't need to stay up to date. Just for reference.

    scope_name = 'User'
    timezone = timezone_pref
    language = language_pref

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        return (await cls.update_or_create(id=ctx.author.id, name=f'{ctx.author.name}#{ctx.author.discriminator}'))[0]

    def __str__(self):
        return f'{self.name} ({self.id})'
