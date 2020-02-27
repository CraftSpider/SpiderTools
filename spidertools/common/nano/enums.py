
import enum


class PrivacyOptions(enum.IntEnum):
    """
        Possible privacy setting selections
    """
    ANYONE = 2
    BUDDIES = 1
    PRIVATE = 0


class GroupType(enum.Enum):
    """
        Possible types a group can be
    """
    REGION = "region"
    EVERYONE = "everyone"
    BUDDIES = "buddies"


class EventType(enum.IntEnum):
    """
        Possible types an event can be
    """
    NANOWRIMO = 0
    CAMP_NANO = 1


class EntryMethod(enum.Enum):
    """
        Possible ways a user could have joined a group
    """
    JOINED = "join"
    CREATED = "creator"
    INVITED = "invited"
