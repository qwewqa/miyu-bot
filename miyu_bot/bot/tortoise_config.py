TORTOISE_ORM = {
    'connections': {'default': 'postgres://postgres@localhost/miyu'},
    'apps': {
        'models': {
            'models': ['miyu_bot.bot.models', 'aerich.models'],
            'default_connection': 'default',
        },
    },
}
