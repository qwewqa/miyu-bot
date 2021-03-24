# Miyu Bot
A Discord utility bot for mobile rhythm game D4DJ Groovy Mix.


## Setup

### d4dj-utils
Miyu Bot depends on [d4dj-utils](https://github.com/qwewqa/d4dj-utils),
which should visible via the PYTHONPATH, or a `.pth` file in a venv.
Some functionality of d4dj-utils is not fully public, such as some chart related functions or asset downloading and decryption,
and is considered "extended" functionality.

### Bot token
A JSON file called `config.json` should created in the working directory
containing a dict with a single key `"token"` corresponding to the bot token.

### Database initialization
Edit the tortoise configuration file at `miyu_bot/bot/tortoise_config.py`
for whichever database is preferred.
SQLite suffices for development, but may have issues with migrations,
so PostgreSQL is recommended for general use.

Files in the `migrations` folder are used by [aerich](https://github.com/tortoise/aerich)
and are meant for use with PostgreSQL.

Before running the bot for the first time, execute `init_db.py` to
initialize the database.

### Assets
At a minimum, the bot requires decrypted and decompressed master files
in the working directory at `assets/Master`. 

If extended functions of d4dj-utils are available, `update_assets.py` 
may be used to download or update assets to the latest version and to
perform the necessary decryption and decompression.

`export_assets.py` is used to export assets to the `export` directory for
online hosting.


## Information
Miyu Bot may be added to a server using the [invite link](https://discord.com/api/oauth2/authorize?client_id=789314370999287808&permissions=388160&scope=bot).

Questions may be asked in the [bot server](https://discord.gg/TThMwrAZTR),
or by contacting qwewqa#3948 on Discord.
