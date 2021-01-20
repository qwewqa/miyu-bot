import pytz
from pytz import UnknownTimeZoneError

from miyu_bot.commands.common.argument_parsing import ArgumentError


def get_timezone(arguments, default='Asia/Tokyo'):
    timezone_name, _ = arguments.single(['timezone', 'tz'], default=default, allowed_operators=['='])
    try:
        return pytz.timezone(timezone_name)
    except UnknownTimeZoneError:
        raise ArgumentError(f'Invalid timezone "{timezone_name}", '
                            f'see <https://kevinnovak.github.io/Time-Zone-Picker/> for an interactive map.')