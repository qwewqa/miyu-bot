from pathlib import Path

from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.chart_master import ChartMaster
from d4dj_utils.master.event_master import EventMaster
from d4dj_utils.master.music_master import MusicMaster

from miyu_bot.bot.master_asset_manager import hash_master


def _get_asset_path(master, parent, path):
    return str((Path(parent) / f'{path.stem}_{hash_master(master)}{path.suffix}').as_posix())


music_dir = Path('.') / 'music'
chart_dir = music_dir / 'charts'
jacket_dir = music_dir / 'jacket'
card_dir = Path('.') / 'cards'
card_icon_dir = card_dir / 'icons'
card_art_dir = card_dir / 'art'
event_dir = Path('.') / 'events'
event_logo_dir = event_dir / 'logos'


def get_music_jacket_path(music: MusicMaster):
    return _get_asset_path(music, jacket_dir, music.jacket_path)


def get_chart_image_path(chart: ChartMaster):
    return _get_asset_path(chart, chart_dir, chart.image_path)


def get_chart_mix_path(chart: ChartMaster):
    return _get_asset_path(chart, chart_dir, chart.mix_path)


def get_card_art_path(card: CardMaster, lb):
    return _get_asset_path(card, card_art_dir, card.art_path(lb))


def get_card_icon_path(card: CardMaster, lb):
    return _get_asset_path(card, card_icon_dir, card.icon_path(lb))


def get_event_logo_path(event: EventMaster):
    return _get_asset_path(event, event_logo_dir, event.logo_path)
