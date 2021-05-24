import argparse
import asyncio
import logging
import logging.config

from d4dj_utils.extended.manager.revision_manager import RevisionManager
from d4dj_utils.master.asset_manager import AssetManager


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


if __name__ == '__main__':
    asyncio.run(main())
