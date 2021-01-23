import shutil
from pathlib import Path

from d4dj_utils.manager.asset_manager import AssetManager

from miyu_bot.bot.master_asset_manager import hash_master
from miyu_bot.commands.common.asset_paths import *


def main():
    target_dir = Path('./export')
    target_dir.mkdir(parents=True, exist_ok=True)

    asset_manager = AssetManager('assets')

    (target_dir / music_dir).mkdir(exist_ok=True)
    (target_dir / chart_dir).mkdir(exist_ok=True)
    (target_dir / jacket_dir).mkdir(exist_ok=True)
    (target_dir / card_dir).mkdir(exist_ok=True)
    (target_dir / card_icon_dir).mkdir(exist_ok=True)
    (target_dir / card_art_dir).mkdir(exist_ok=True)
    (target_dir / event_dir).mkdir(exist_ok=True)
    (target_dir / event_logo_dir).mkdir(exist_ok=True)

    for music in asset_manager.music_master.values():
        try:
            shutil.copy(music.jacket_path, target_dir / get_music_jacket_path(music))
        except FileNotFoundError:
            pass
        for chart in music.charts.values():
            try:
                shutil.copy(chart.image_path, target_dir / get_chart_image_path(chart))
                shutil.copy(chart.image_path, target_dir / get_chart_mix_path(chart))
            except FileNotFoundError:
                pass

    for card in asset_manager.card_master.values():
        try:
            for lb in range(2):
                shutil.copy(card.art_path(lb), target_dir / get_card_art_path(card, lb))
                shutil.copy(card.icon_path(lb), target_dir / get_card_icon_path(card, lb))
        except FileNotFoundError:
            pass

    for event in asset_manager.event_master.values():
        try:
            shutil.copy(event.logo_path, target_dir / get_event_logo_path(event))
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
