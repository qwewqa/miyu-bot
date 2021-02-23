from tortoise import Tortoise, run_async

from miyu_bot.bot.models import TORTOISE_ORM


async def init():
    await Tortoise.init(TORTOISE_ORM)
    await Tortoise.generate_schemas()


run_async(init())
