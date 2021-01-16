import hashlib
import shutil
from pathlib import Path

from d4dj_utils.manager.asset_manager import AssetManager
from d4dj_utils.master.master_asset import MasterAsset

from miyu_bot.commands.common.master_asset_manager import MasterFilterManager, hash_master


def main():
    target_dir = Path('./export')
    target_dir.mkdir(parents=True, exist_ok=True)

    asset_manager = AssetManager('assets')

    music_dir = target_dir / 'music'
    chart_dir = music_dir / 'charts'
    card_dir = target_dir / 'cards'
    card_icon_dir = card_dir / 'icons'
    card_art_dir = card_dir / 'art'
    event_dir = target_dir / 'events'
    event_logo_dir = event_dir / 'logos'

    music_dir.mkdir(exist_ok=True)
    chart_dir.mkdir(exist_ok=True)
    card_dir.mkdir(exist_ok=True)
    card_icon_dir.mkdir(exist_ok=True)
    card_art_dir.mkdir(exist_ok=True)
    event_dir.mkdir(exist_ok=True)
    event_logo_dir.mkdir(exist_ok=True)

    for music in asset_manager.music_master.values():
        for chart in music.charts.values():
            try:
                chart_hash = hash_master(chart)
                chart_path = chart.image_path
                target_path = chart_dir / f'{chart_path.stem}_{chart_hash}{chart_path.suffix}'
                shutil.copy(chart_path, target_path)
            except FileNotFoundError:
                pass

    for card in asset_manager.card_master.values():
        card_hash = hash_master(card)
        try:
            for lb in range(2):
                art_path = card.art_path(lb)
                art_target = card_art_dir / f'{art_path.stem}_{card_hash}{art_path.suffix}'
                icon_path = card.icon_path(lb)
                icon_target = card_icon_dir / f'{icon_path.stem}_{card_hash}{icon_path.suffix}'
                shutil.copy(art_path, art_target)
                shutil.copy(icon_path, icon_target)
        except FileNotFoundError:
            pass

    for event in asset_manager.event_master.values():
        try:
            event_hash = hash_master(event)
            logo_path = event.logo_path
            logo_target = event_logo_dir / f'{logo_path.stem}_{event_hash}{logo_path.suffix}'
            shutil.copy(logo_path, logo_target)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    main()
