import asyncio
import logging
import logging.config

from d4dj_utils.manager.asset_manager import AssetManager
from d4dj_utils.manager.revision_manager import RevisionManager


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    revision_manager = RevisionManager('assets')
    await revision_manager.repair_downloads()
    await revision_manager.update_assets()
    manager = AssetManager('assets')
    manager.render_charts_by_master()

    for music in manager.music_master.values():
        if not music.audio_path.with_name(music.audio_path.name + '.wav').exists():
            music.decode_audio()
            logger.info(f'Decoded audio for {music.name}.')


if __name__ == '__main__':
    asyncio.run(main())
