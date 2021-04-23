import shutil
from pathlib import Path

from miyu_bot.commands.common.asset_paths import get_asset_filename


def main():
    base_path = Path('assets')
    target_path = Path('export')

    asset_paths = [
        'music_jacket/*.jpg',
        'ondemand/card_chara/*.jpg',
        'ondemand/card_icon/*.jpg',
        'ondemand/chart/*.png',
        'ondemand/event/*/*.jpg',
        'ondemand/event/*/*.png',
        'ondemand/gacha/top/banner/*.png'
        'ondemand/loginBonus/*.jpg'
    ]

    for asset_path in asset_paths:
        for path in base_path.glob(asset_path):
            target_file = target_path / get_asset_filename(path)
            if not target_file.exists():
                shutil.copy(path, target_file)


if __name__ == '__main__':
    main()
