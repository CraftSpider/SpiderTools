
import enum


class PrivacyOptions(enum.IntEnum):
    ANYONE = 2
    BUDDIES = 1
    PRIVATE = 0


class GroupType(enum.Enum):
    REGION = "region"
    EVERYONE = "everyone"
    BUDDIES = "buddies"


class EventType(enum.IntEnum):
    NANOWRIMO = 0
    CAMP_NANO = 1


class EntryMethod(enum.Enum):
    JOINED = "join"
    CREATED = "creator"
    INVITED = "invited"
