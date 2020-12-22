import asyncio
import logging
import logging.config

from d4dj_utils.manager.asset_manager import AssetManager
from d4dj_utils.manager.revision_manager import RevisionManager


async def main():
    logging.basicConfig(level=logging.INFO)
    revision_manager = RevisionManager('assets')
    await revision_manager.repair_downloads()
    await revision_manager.update_assets()
    manager = AssetManager('assets')
    manager.render_charts_by_master()


if __name__ == '__main__':
    asyncio.run(main())
