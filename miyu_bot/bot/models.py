import copy
import datetime
from abc import abstractmethod
from typing import ClassVar, Callable, Any, Optional, Dict, Type, Tuple, Union

import pytz
from discord.ext import commands
from tortoise import Model, fields
from tortoise.expressions import F
from tortoise.models import ModelMeta

from miyu_bot.bot.servers import Server, SERVER_NAMES
from miyu_bot.commands.master_filter.locales import lowercase_locale_mapping


class Preference:
    name: str
    attribute_name: str
    scope: "PreferenceScope"

    def __init__(
        self,
        name: str,
        field: fields.Field,
        default_value: Any,
        unset_value: Any = None,
        *,
        validator: Callable[[str], Union[bool, str, None]] = lambda _v: None,
        transformer: Callable[[str], Any] = lambda v: v,
        load_converter: Callable[[Any], Any] = lambda v: v,
        is_privileged: bool = False,
    ):
        self.name = name
        self.field = field
        self.default_value = default_value
        self.unset_value = unset_value
        self._validator = validator
        self._transformer = transformer
        self._load_converter = load_converter
        self.is_privileged = is_privileged

    def validate_or_get_error_message(self, value: str) -> Optional[str]:
        value = self._validator(value)
        if isinstance(value, bool) and value:
            return "Validation error."
        elif isinstance(value, str):
            return value
        return None

    def transform(self, value: str) -> Any:
        return self._transformer(value)

    def convert(self, value: Any) -> Any:
        return self._load_converter(value)


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
                        raise AttributeError(
                            f"Encountered multiple preferences globally with name {k}."
                        )
                else:
                    all_preferences[v.name] = v
                v = copy.deepcopy(v)
                v.attribute_name = k
                if k in preferences:
                    raise AttributeError(
                        f"Encountered multiple preferences in a model with name {k}."
                    )
                preferences[k] = v
        for k, v in preferences.items():
            attrs[k] = v.field
        attrs["preferences"] = preferences
        return super().__new__(mcs, name, bases, attrs)


class PreferenceScope(Model, metaclass=PreferenceScopeMeta):
    scope_name: ClassVar[str] = "Unnamed"
    preferences: ClassVar[Dict[str, "Preference"]]

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
        return preference.convert(value)

    def preference_set(self, name):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        value = getattr(self, preference.attribute_name)
        return value != preference.unset_value

    def get_preference_no_convert(self, name):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        value = getattr(self, preference.attribute_name)
        if value == preference.unset_value:
            return None
        return value

    def set_preference(self, name, value):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        setattr(self, preference.attribute_name, preference.transform(value))

    def clear_preference(self, name):
        if name not in self.preferences:
            raise KeyError(f'Unknown preference "{name}".')
        preference = self.preferences[name]
        setattr(self, preference.attribute_name, preference.unset_value)

    @staticmethod
    def has_permissions(ctx: commands.Context) -> bool:
        return True


lowercase_tzs = {tz.lower() for tz in pytz.all_timezones_set}

bool_true_strings = {"True", "true", "T", "t", "1", "Yes", "yes"}
bool_false_strings = {"False", "false", "F", "f", "0", "No", "no"}
bool_strings = bool_true_strings | bool_false_strings


def validate_boolean(v: str):
    if v not in bool_strings:
        return "Not a valid boolean"


def transform_boolean(v: str):
    return v in bool_true_strings  # Assumes already validated


# In minutes. Should be evenly divisible with respect to 24 hours.
valid_loop_intervals = [1, 2, 5, 10, 20, 30, 60, 120]


def validate_loop_interval(v: str):
    if not v.isnumeric():
        return "Not an integer."
    v = float(v)
    if not v.is_integer():
        return "Not an integer."
    v = int(v)
    if v not in valid_loop_intervals:
        return "Must be 1, 2, 5, 10, 20, 30, 60, or 120. Use clearpref to remove."


timezone_pref = Preference(
    "timezone",
    fields.CharField(max_length=31, null=True),
    default_value=pytz.timezone("etc/utc"),
    validator=lambda tz: None if tz.lower() in lowercase_tzs else "Invalid timezone.",
    transformer=lambda tz: tz.lower(),
    load_converter=lambda tz: pytz.timezone(tz),
)
language_pref = Preference(
    "language",
    fields.CharField(max_length=15, null=True),
    default_value="en-US",
    validator=lambda lang: None
    if lang.lower() in lowercase_locale_mapping
    else "Invalid language.",
    transformer=lambda lang: lowercase_locale_mapping[lang.lower()],
)
prefix_pref = Preference(
    "prefix",
    fields.CharField(max_length=63, null=True),
    default_value="!",
    validator=lambda pfx: (
        None
        if 1 <= len(pfx) <= 63
        else "Invalid prefix length. Should be between 1 and 63 characters."
    ),
)
loop_pref = Preference(
    "loop",
    fields.IntField(null=True, index=True),
    default_value=None,
    validator=validate_loop_interval,
    transformer=lambda v: int(v),
)
leaks_pref = Preference(
    "leaks",
    fields.BooleanField(null=True),
    default_value=False,
    validator=validate_boolean,
    transformer=transform_boolean,
    is_privileged=True,
)
server_pref = Preference(
    "server",
    fields.IntEnumField(Server, null=True),
    default_value=Server.JP,
    validator=lambda v: None if v.lower() in SERVER_NAMES else "Invalid server.",
    transformer=lambda v: SERVER_NAMES[v.lower()],
)


class Guild(PreferenceScope):
    id = fields.BigIntField(pk=True)

    scope_name = "Guild"
    timezone = timezone_pref
    language = language_pref
    prefix = prefix_pref
    server = server_pref

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        if not ctx.guild:
            return None
        return (await cls.get_or_create(id=ctx.guild.id))[0]

    def __str__(self):
        return f"Guild({self.id})"

    @staticmethod
    def has_permissions(ctx: commands.Context) -> bool:
        return ctx.author.guild_permissions.manage_channels


class Channel(PreferenceScope):
    id = fields.BigIntField(pk=True)

    scope_name = "Channel"
    timezone = timezone_pref
    language = language_pref
    loop = loop_pref
    leaks = leaks_pref
    server = server_pref

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        return (await cls.get_or_create(id=ctx.channel.id))[0]

    def __str__(self):
        return f"Channel({self.id})"

    @staticmethod
    def has_permissions(ctx: commands.Context) -> bool:
        return ctx.author.guild_permissions.manage_channels


class User(PreferenceScope):
    id = fields.BigIntField(pk=True)

    scope_name = "User"
    timezone = timezone_pref
    language = language_pref
    prefix = prefix_pref
    leaks = leaks_pref
    server = server_pref

    @classmethod
    async def get_from_context(cls, ctx: commands.Context):
        return (await cls.get_or_create(id=ctx.author.id))[0]

    def __str__(self):
        return f"User({self.id})"


class GachaState(Model):
    user_id = fields.BigIntField()
    server_id = fields.IntField()
    gacha_id = fields.IntField()
    pity_counter = fields.IntField(default=0)
    total_counter = fields.IntField(default=0)
    total_roll_counter = fields.IntField(default=0)

    class Meta:
        unique_together = (("user_id", "server_id", "gacha_id"),)


class CollectionEntry(Model):
    user_id = fields.BigIntField(index=True)
    server_id = fields.IntField()
    gacha_id = fields.IntField()
    table_rate_id = fields.IntField()
    card_id = fields.IntField()
    first_pulled = fields.IntField(default=0)
    first_pulled_roll = fields.IntField(default=0)
    counter = fields.IntField(default=0)

    class Meta:
        unique_together = (
            ("user_id", "server_id", "gacha_id", "table_rate_id", "card_id"),
        )


class CommandUsageCount(Model):
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=31)
    counter = fields.IntField(default=0)
    date = fields.DateField(default=datetime.date(year=2021, month=1, day=1))

    class Meta:
        unique_together = (("guild_id", "name", "date"),)


class GeneralUsageCount(Model):
    name = fields.TextField()
    date = fields.DateField()
    counter = fields.IntField(default=0)

    class Meta:
        unique_together = (("name", "date"),)


async def log_usage(name: str):
    cnt, _ = await GeneralUsageCount.get_or_create(
        name=name, date=datetime.datetime.utcnow().date()
    )
    cnt.counter = F("counter") + 1
    await cnt.save()
