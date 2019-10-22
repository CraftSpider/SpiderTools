
import enum

class PrivacyOptions(enum.IntEnum):
    ANYONE: int = enum.auto()
    BUDDIES: int = enum.auto()
    PRIVATE: int = enum.auto()

class GroupType(enum.Enum):
    REGION: str = enum.auto()
    EVERYONE: str = enum.auto()
    BUDDIES: str = enum.auto()

class EventType(enum.IntEnum):
    NANOWRIMO: int = enum.auto()
    CAMP_NANO: int = enum.auto()

class EntryMethod(enum.Enum):
    JOINED: str = enum.auto()
    CREATED: str = enum.auto()
    INVITED: str = enum.auto()
