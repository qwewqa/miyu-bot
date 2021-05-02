import argparse
import asyncio
import logging
import logging.config
import os

from d4dj_utils.extended.tools.tools import extract_hca, vgmstream
from d4dj_utils.master.asset_manager import AssetManager
from d4dj_utils.extended.manager.revision_manager import RevisionManager


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('version', type=str)
    parser.add_argument('server', type=str)
    args = parser.parse_args()

    if args.server == 'jp':
        asset_path = 'assets'
        base_url = f'https://resources.d4dj-groovy-mix.com/{args.version}/'
    elif args.server == 'en':
        asset_path = 'assets_en'
        base_url = ''
        raise
    else:
        raise

    revision_manager = RevisionManager(asset_path, base_url)
    await revision_manager.repair_downloads()
    await revision_manager.update_assets()
    manager = AssetManager(asset_path)
    manager.render_charts_by_master()

    for root, dirs, files in os.walk(asset_path):
        if 'adv' in root or 'music' in root:
            continue
        for file in files:
            if file.endswith(".acb"):
                try:
                    extract_hca(os.path.join(root, file))
                except Exception as e:
                    logger.warning(f'Failed to extract audio {os.path.join(root, file)}: {e}')

    for root, dirs, files in os.walk(asset_path):
        for file in files:
            if file.endswith(".hca"):
                path = os.path.join(root, file)
                if os.path.exists(path + '.wav'):
                    continue
                vgmstream(path)
                logger.info(f'Decoded audio {path}.')

    for music in manager.music_master.values():
        if not music.audio_path.with_name(music.audio_path.name + '.wav').exists():
            music.decode_audio()
            logger.info(f'Decoded audio for {music.name}.')


if __name__ == '__main__':
    asyncio.run(main())
