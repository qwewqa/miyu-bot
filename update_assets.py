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
    revision_manager = RevisionManager('assets')
    await revision_manager.repair_downloads()
    await revision_manager.update_assets()
    manager = AssetManager('assets')
    manager.render_charts_by_master()

    for root, dirs, files in os.walk('assets'):
        if 'adv' in root or 'music' in root:
            continue
        for file in files:
            if file.endswith(".acb"):
                try:
                    extract_hca(os.path.join(root, file))
                except Exception as e:
                    logger.warning(f'Failed to extract audio {os.path.join(root, file)}: {e}')

    for root, dirs, files in os.walk('assets'):
        for file in files:
            if file.endswith(".hca"):
                path = os.path.join(root, file)
                if os.path.exists(path + '.wav'):
                    continue
                vgmstream(path)
                logger.info(f'Decoded audio {path}.')


if __name__ == '__main__':
    asyncio.run(main())
