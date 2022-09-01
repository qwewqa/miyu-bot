import random
from pathlib import Path

from miyu_bot.bot.bot import MiyuBot
from miyu_bot.commands.docs.info_command_docs import generate_info_command_docs
from timeit import default_timer as timer

from miyu_bot.commands.docs.utility_command_docs import generate_utility_command_docs

if __name__ == '__main__':
    start = timer()

    bot = MiyuBot('assets', gen_doc=True, command_prefix='!')
    bot.gen_doc = True

    await bot.load_extension('miyu_bot.commands.cogs.info')
    await bot.load_extension('miyu_bot.commands.cogs.card')
    await bot.load_extension('miyu_bot.commands.cogs.event')
    await bot.load_extension('miyu_bot.commands.cogs.music')
    # Other cog will not have generated docs
    # await bot.load_extension('miyu_bot.commands.cogs.other')
    await bot.load_extension('miyu_bot.commands.cogs.preferences')
    await bot.load_extension('miyu_bot.commands.cogs.audio')
    await bot.load_extension('miyu_bot.commands.cogs.gacha')

    random.seed(0)

    generate_info_command_docs(bot, Path(__file__).parent / 'docs/commands/info', bot.cogs['Info'].master_filters)
    generate_utility_command_docs(bot, Path(__file__).parent / 'docs/commands/utility')

    print(f'Generated docs in {timer() - start}s.')
