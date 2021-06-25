from pathlib import Path

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.docs.info_doc_generation import generate_info_command_docs
from timeit import default_timer as timer

if __name__ == '__main__':
    start = timer()

    bot = D4DJBot('assets', command_prefix='!')
    bot.gen_doc = True

    bot.load_extension('miyu_bot.commands.cogs.info')
    bot.load_extension('miyu_bot.commands.cogs.card')
    bot.load_extension('miyu_bot.commands.cogs.event')
    bot.load_extension('miyu_bot.commands.cogs.music')
    bot.load_extension('miyu_bot.commands.cogs.utility')
    bot.load_extension('miyu_bot.commands.cogs.preferences')
    bot.load_extension('miyu_bot.commands.cogs.audio')
    bot.load_extension('miyu_bot.commands.cogs.gacha')
    generate_info_command_docs(bot, Path(__file__).parent / 'docs/commands/info', bot.cogs['Info'].master_filters)

    print(f'Generated docs in {timer() - start}s.')
