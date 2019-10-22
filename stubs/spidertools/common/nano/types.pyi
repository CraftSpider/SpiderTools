
from typing import Dict, Type, Any, Optional, List, NoReturn, Tuple, _GenericAlias, Callable
import datetime as dt
import spidertools.common.nano.state as state
from spidertools.common.nano.enums import *


def _from_iso(s: str) -> dt.datetime: ...

def _from_date(s: str) -> dt.date: ...

def _from_tz(s: int) -> dt.timezone: ...

def _is_dunder(s: str) -> bool: ...

def _get_convert(type: type) -> Callable[[Any], Any]: ...

_Null: object = ...

class NanoMeta(type):

    def __new__(mcs, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]) -> 'NanoMeta':
        return super().__new__(mcs, name, bases, namespace)

class NanoObj(metaclass=NanoMeta):

    __slots__ = ("_state", "_relationships", "_self", "id")

    TYPE_MAP: Dict[str, Type['NanoObj']] = ...
    TYPE: str
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    _state: state.NanoState
    _relationships: Dict[str, str]
    _self: str
    id: int

    def __init__(self, state: state.NanoState, data: Dict[str, Any]) -> None: ...

    def __init_subclass__(cls: Type['NanoObj'], **kwargs: Any) -> None: ...

    def _do_convert(self, attr: _GenericAlias, data: Dict[str, Any]): ...

    def _from_data(self, data: Dict[str, Any]) -> None: ...

    async def update(self) -> None: ...

class Subdata: ...

class PrivacySettings(Subdata):

    __slots__ = ("view_buddies", "view_projects", "view_profile", "view_search", "send_messages", "visibility_regions",
                 "visibility_buddies", "visibility_activity")

    view_buddies: PrivacyOptions
    view_projects: PrivacyOptions
    view_profile: PrivacyOptions
    view_search: PrivacyOptions
    send_messages: PrivacyOptions
    visibility_regions: bool
    visibility_buddies: bool
    visibility_activity: bool

    def __init__(self, data: Dict[str, Any]) -> None: ...

class NotificationSettings(Subdata):

    __slots__ = ("buddy_requests", "buddy_activities", "buddy_messages", "ml_messages", "hq_messages",
                 "sprint_invitation", "sprint_start", "writing_reminders", "goal_milestones", "home_region_events",
                 "new_badges")

    buddy_requests: bool
    buddy_activities: bool
    buddy_messages: bool
    ml_messages: bool
    hq_messages: bool
    sprint_invitation: bool
    sprint_start: bool
    writing_reminders: bool
    goal_milestones: bool
    home_region_events: bool
    new_badges: bool

class EmailSettings(Subdata):

    __slots__ = ("buddy_requests", "buddy_messages", "ml_messages", "hq_messages", "blog_posts", "newsletter",
                 "home_region_events", "writing_reminders")

    buddy_requests: bool
    buddy_messages: bool
    ml_messages: bool
    hq_messages: bool
    blog_posts: bool
    newsletter: bool
    home_region_events: bool
    writing_reminders: bool

    def __init__(self, data: Dict[str, Any]) -> None: ...


class UserStats(Subdata):

    __slots__ = ("projects", "projects_enabled", "streak", "streak_enabled", "word_count", "word_count_enabled",
                 "wordiest", "wordiest_enabled", "writing_pace", "writing_pace_enabled", "years_done", "years_won",
                 "years_enabled")

    projects: int
    projects_enabled: bool
    streak: int
    streak_enabled: bool
    word_count: int
    word_count_enabled: bool
    wordiest: int
    wordiest_enabled: bool
    writing_pace: int
    writing_pace_enabled: bool
    years_done: int
    years_won: int
    years_enabled: bool

    def __init__(self, data: Dict[str, Any]) -> None: ...

class Funds:

    __slots__ = ("goal", "raised", "donors")

    goal: int
    raised: float
    donors: int

    def __init__(self, data: Dict[str, Any]) -> None: ...


class NanoUser(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    name: str
    slug: str
    time_zone: str
    postal_code: Optional[str]
    bio: str
    created_at: dt.datetime
    email: str
    location: Optional[str]
    privacy_settings: PrivacySettings
    notification_settings: NotificationSettings
    email_settings: EmailSettings
    stats: UserStats
    halo: bool
    laurels: int
    avatar: Optional[str]
    plate: Optional[str]

    _external_links: Optional[List['NanoExternalLink']]
    _favorite_books: Optional[List['NanoFavoriteBook']]
    _favorite_authors: Optional[List['NanoFavoriteAuthor']]
    _genres: Optional[List['NanoGenre']]
    _project_sessions: Optional[List['NanoProjectSession']]
    _group_users: Optional[List['NanoGroupUser']]
    _groups: Optional[List['NanoGroup']]
    _timers: Optional[List['NanoTimer']]
    _nanomessages: Optional[List['NanoMessage']]
    _stopwatches: Optional[List['NanoStopwatch']]
    _user_badges: Optional[List['NanoUserBadge']]
    _projects: Optional[List['NanoProject']]
    _project_challenges: Optional[List['NanoProjectChallenge']]

    async def get_external_links(self) -> List['NanoExternalLink']: ...

    async def get_favorite_books(self) -> List['NanoFavoriteBook']: ...

    async def get_favorite_authors(self) -> List['NanoFavoriteAuthor']: ...

    async def get_genres(self) -> List['NanoGenre']: ...

    async def get_project_sessions(self) -> List['NanoProjectSession']: ...

    async def get_group_users(self) -> List['NanoGroupUser']: ...

    async def get_groups(self) -> List['NanoGroup']: ...

    async def get_timers(self) -> List['NanoTimer']: ...

    async def get_nanomessages(self) -> List['NanoMessage']: ...

    async def get_stopwatches(self) -> List['NanoStopwatch']: ...

    async def get_user_badges(self) -> List['NanoUserBadge']: ...

    async def get_projects(self) -> List['NanoProject']: ...

    async def get_project_challenges(self) -> List['NanoProjectChallenge']: ...

class NanoProject(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    user_id: int
    title: str
    slug: str
    unit_type: int
    excerpt: str
    created_at: dt.datetime
    summary: str
    pinterest: Optional[str]
    playlist: Optional[str]
    privacy: bool
    primary: bool
    status: str
    cover: Optional[str]

    _genres: Optional[List['NanoGenre']]
    _project_challenges: Optional[List['NanoChallenge']]
    _project_sessions: Optional[List['NanoProjectSession']]
    _challenges: Optional[List['NanoChallenge']]
    _user: Optional['NanoUser']

    async def get_user(self) -> 'NanoUser': ...

    async def get_genres(self) -> List['NanoGenre']: ...

    async def get_project_challenges(self) -> List['NanoProjectChallenge']: ...

    async def get_project_sessions(self) -> List['NanoProjectSession']: ...

    async def get_challenges(self) -> List['NanoChallenge']: ...

    async def edit_details(self, *, title: Optional[str] = ..., unit_type: Optional[int] = ..., excerpt: Optional[str] = ..., summary: Optional[str] = ..., pinterest: Optional[str] = ...,
                           playlist: Optional[str] = ..., privacy: PrivacyOptions = ..., primary: bool = ..., status: Optional[str] = ..., cover: Optional[str] = ...) -> None: ...

class NanoFavoriteBook(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    title: str
    user_id: int

    _user: Optional['NanoUser']

    async def get_user(self) -> 'NanoUser': ...

class NanoFavoriteAuthor(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    name: str
    user_id: int

    _user: Optional['NanoUser']

    async def get_user(self) -> 'NanoUser': ...

class NanoUserBadge(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    badge_id: int
    user_id: int
    project_challenge_id: int
    created_at: dt.datetime

    _user: Optional['NanoUser']
    _badge: Optional['NanoBadge']

    async def get_user(self) -> 'NanoUser': ...

    async def get_badge(self) -> 'NanoBadge': ...

class NanoBadge(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    title: str
    list_order: int
    suborder: Optional[int]
    badge_type: str
    adheres_to: Any
    description: str
    awarded_description: str
    generic_description: str
    active: bool
    unawarded: str
    awarded: str

class NanoGenre(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    name: str
    user_id: int

    _user: Optional['NanoUser']

    async def get_user(self) -> 'NanoUser': ...

class NanoProjectSession(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    start: str
    end: str
    count: Optional[int]
    how: Optional[Any]
    where: Optional[Any]
    feeling: Optional[Any]
    created_at: dt.datetime
    unit_type: int
    project_id: int

    _project: Optional['NanoProject']
    _project_challenge: Optional[List['NanoProjectChallenge']]

    async def get_project(self) -> 'NanoProject': ...

    async def get_project_challenge(self) -> List['NanoProjectChallenge']: ...

class NanoGroup(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    name: str
    slug: str
    group_type: GroupType
    description: str
    longitude: float
    latitude: float
    member_count: int
    user_id: int
    group_id: int
    time_zone: str
    created_at: dt.datetime
    updated_at: dt.datetime
    start_dt: str
    end_dt: str
    approved_by_id: int
    url: str
    plate: str

    _user: Optional['NanoUser']
    _external_links: Optional[List['NanoGroupExternalLink']]
    _users: Optional[List['NanoUser']]
    _nanomessages: Optional[List['NanoMessage']]
    _location_groups: Optional[List['NanoLocationGroup']]
    _locations: Optional[List['NanoLocation']]

    async def get_user(self) -> Optional['NanoUser']: ...

    async def get_external_links(self) -> List['NanoGroupExternalLink']: ...

    async def get_users(self) -> List['NanoUser']: ...

    async def get_nanomessages(self) -> List['NanoMessage']: ...

    async def get_location_groups(self) -> List['NanoLocationGroup']: ...

    async def get_locations(self) -> List['NanoLocation']: ...

class NanoGroupUser(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    created_at: dt.datetime
    updated_at: dt.datetime
    group_code_id: int
    is_admin: bool
    invited_by_id: Optional[int]
    invitation_accepted: bool
    group_id: int
    user_id: int
    primary: bool
    joined_at: str
    join_method: str
    left_at: str
    left_method: str
    group_type: GroupType
    unread_messages: int

    _group: Optional['NanoGroup']
    _user: Optional['NanoUser']
    _inviter: Optional['NanoUser']

    async def get_user(self) -> 'NanoUser': ...

    async def get_group(self) -> 'NanoGroup': ...

    async def get_inviter(self) -> Optional['NanoUser']: ...

class NanoProjectChallenge(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    project_id: int
    starts_at: str
    ends_at: str
    challenge_id: int
    start_count: int
    current_count: int
    goal: int
    unit_type: int
    name: str
    nano_event: bool
    latest_count: int

    _project: Optional['NanoProject']
    _challenge: Optional['NanoChallenge']
    _project_sessions: Optional[List['NanoProjectSession']]
    _user_badges: Optional[List['NanoUserBadge']]

    async def get_project(self) -> 'NanoProject': ...

    async def get_challenge(self) -> 'NanoChallenge': ...

    async def get_project_sessions(self) -> List['NanoProjectSession']: ...

    async def get_user_badges(self) -> List['NanoUserBadge']: ...

    async def get_stats(self) -> NoReturn: ...

class NanoChallenge(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    event_type: EventType
    start: str
    end: str
    unit_type: int
    default_goal: int
    flexible_goal: bool
    writing_type: int
    user_id: int
    name: str
    win_starts: str
    prep_starts: str

    _user: Optional['NanoUser']

    async def get_user(self) -> Optional['NanoUser']: ...

class NanoMessage(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    user_id: int
    group_id: int
    content: str
    created_at: dt.datetime
    updated_at: dt.datetime
    official: bool
    avatar_url: str
    sender_name: str
    sender_slug: str

    _user: Optional['NanoUser']
    _group: Optional['NanoGroup']

    async def get_user(self) -> 'NanoUser': ...

    async def get_group(self) -> 'NanoGroup': ...

class NanoExternalLink(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    url: str
    user_id: int

    _user: Optional['NanoUser']

    async def get_user(self) -> 'NanoUser': ...

class NanoGroupExternalLink(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    url: str
    group_id: int

    _group: Optional['NanoGroup']

    async def get_group(self) -> 'NanoGroup': ...

class NanoLocation(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    name: str
    street1: str
    street2: str
    city: str
    state: str
    country: str
    postal_code: int
    longitude: float
    latitude: float
    formatted_address: str
    map_url: Optional[str]
    county: str
    neighborhood: Optional[str]
    municipality: Optional[str]
    utc_offset: int

class NanoLocationGroup(NanoObj):

    TYPE: str = ...
    _ATTR_DATA: Dict[str, Tuple[type, str]] = ...

    location_id: int
    group_id: int
    primary: bool

    _location: Optional['NanoLocation']
    _group: Optional['NanoGroup']

    async def get_location(self) -> 'NanoLocation': ...

    async def get_group(self) -> 'NanoGroup': ...
