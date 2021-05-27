from enum import IntEnum


class Server(IntEnum):
    JP = 0
    EN = 1


SERVER_NAMES = {
    'jp': Server.JP,
    'japanese': Server.JP,
    'japan': Server.JP,
    'en': Server.EN,
    'english': Server.EN,
}
