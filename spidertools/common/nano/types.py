
import typing
import datetime as dt
from .enums import *


def _from_iso(s):
    if s[-1] == "Z":
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def _from_date(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def _from_tz(s):
    return dt.timezone(dt.timedelta(minutes=s))


def _is_dunder(s):
    return s.startswith("__") and s.endswith("__")


def _get_convert(type):
    if type == dt.datetime:
        return _from_iso
    elif type == dt.date:
        return _from_date
    elif type == dt.timezone:
        return _from_tz
    else:
        return type


_Null = object()


class NanoMeta(type):

    def __new__(mcs, name, bases, namespace):
        new_namespace = {
            "_ATTR_DATA": {}
        }

        for item in namespace:
            if item == "TYPE" or _is_dunder(item) or not isinstance(namespace[item], str):
                new_namespace[item] = namespace[item]
                continue
            kls = lambda x: x
            if "__annotations__" in namespace and item in namespace["__annotations__"]:
                kls = namespace["__annotations__"][item]
            if isinstance(kls, typing._SpecialForm):
                if (kls._name == "Union" or kls._name == "Optional") and not hasattr(kls, "__origin__"):
                    raise AttributeError(f"NanoObj annotation (on {item}) must not be general, must specify classes.")
            new_namespace["_ATTR_DATA"][item] = (kls, namespace[item])
        if "__annotations__" in namespace:
            for item in namespace["__annotations__"]:
                if item not in new_namespace["_ATTR_DATA"]:
                    kls = namespace["__annotations__"][item]
                    if isinstance(kls, typing._SpecialForm):
                        if (kls._name == "Union" or kls._name == "Optional") and not hasattr(kls, "__origin__"):
                            raise AttributeError(f"NanoObj annotation (on {item}) must not be general, must specify classes.")
                    new_namespace["_ATTR_DATA"][item] = (kls, item.replace("_", "-"))

        return super().__new__(mcs, name, bases, new_namespace)


class NanoObj(metaclass=NanoMeta):

    __slots__ = ("_state", "_relationships", "_self", "id")

    TYPE_MAP = {}

    def __init__(self, state, data):
        self._state = state
        self.id = int(data["id"])
        self._self = data["links"]["self"]
        self._relationships = {}
        self._from_data(data["attributes"])
        for key, val in data["relationships"].items():
            self._relationships[key] = val["links"]["related"]
            for i in val.get("data", ()):
                name = f"_{key.replace('-', '_')}"
                if getattr(self, name) is None:
                    setattr(self, name, [])
                getattr(self, name).append(self._state._get_cache_obj(i["type"], int(i["id"])))

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "TYPE"):
            raise TypeError("NanoObj subclasses must provide a TYPE")
        NanoObj.TYPE_MAP[cls.TYPE] = cls

    def _do_convert(self, cls, name, data):
        func = _get_convert(cls)
        if isinstance(func, type) and issubclass(func, Subdata):
            val = func(data)
        elif isinstance(func, typing._GenericAlias):
            val = self._generic_convert(func, name, data)
        else:
            val = data.get(name, _Null)
            if val is _Null:
                raise AttributeError(f"Data for {self.__class__.__name__} doesn't contain attribute {attr[1]}")
            val = func(val)
        return val

    def _generic_convert(self, cls, name, data):
        to_try = cls.__args__

        last_err = None
        val = None
        for item in to_try:
            if item is None:
                return None
            else:
                try:
                    val = self._do_convert(item, name, data)
                    break
                except Exception as e:
                    last_err = e

        if last_err is not None:
            raise last_err from None
        return val

    def _from_data(self, data):
        for name, attr in self._ATTR_DATA.items():
            val = self._do_convert(attr[0], attr[1], data)
            setattr(self, name, val)

    def _to_json(self, type, val, data):  # TODO: Handle complex types
        if isinstance(val, Subdata):
            data.update(val._to_data())
            return _Null
        return val

    def _to_data(self):
        out = {}
        for name, attr in self._ATTR_DATA.items():
            val = getattr(self, name)
            val = self._to_json(attr[0], val, out)
            if val is not _Null:
                out[attr[1]] = val
        return out

    async def edit(self, **kwargs):
        attrs = self._to_data()
        attrs.update(kwargs)
        data = {
            "id": self.id,
            "type": self.TYPE,
            "attributes": attrs
        }
        #  TODO: make/break relationships?
        await self._state.patch_obj(self, data)

    async def update(self):
        await self._state.update(self)


class Subdata:

    def _to_data(self):
        return {}  # TODO


class PrivacySettings(Subdata):

    __slots__ = ("view_buddies", "view_projects", "view_profile", "view_search", "send_messages", "visibility_regions",
                 "visibility_buddies", "visibility_activity")

    def __init__(self, data):
        self.view_buddies = PrivacyOptions(data["privacy-view-buddies"])
        self.view_projects = PrivacyOptions(data["privacy-view-projects"])
        self.view_profile = PrivacyOptions(data["privacy-view-profile"])
        self.view_search = PrivacyOptions(data["privacy-view-search"])
        self.send_messages = PrivacyOptions(data["privacy-send-nanomessages"])
        self.visibility_regions = data["privacy-visibility-regions"]
        self.visibility_buddies = data["privacy-visibility-buddy-lists"]
        self.visibility_activity = data["privacy-visibility-activity-logs"]


class NotificationSettings(Subdata):

    __slots__ = ("buddy_requests", "buddy_activities", "buddy_messages", "ml_messages", "hq_messages",
                 "sprint_invitation", "sprint_start", "writing_reminders", "goal_milestones", "home_region_events",
                 "new_badges")

    def __init__(self, data):
        self.buddy_requests = data["notification-buddy-requests"]
        self.buddy_activities = data["notification-buddy-activities"]
        self.buddy_messages = data["notification-nanomessages-buddies"]
        self.ml_messages = data["notification-nanomessages-mls"]
        self.hq_messages = data["notification-nanomessages-hq"]
        self.sprint_invitation = data["notification-sprint-invitation"]
        self.sprint_start = data["notification-sprint-start"]
        self.writing_reminders = data["notification-writing-reminders"]
        self.goal_milestones = data["notification-goal-milestones"]
        self.home_region_events = data["notification-events-in-home-region"]
        self.new_badges = data["notification-new-badges"]


class EmailSettings(Subdata):

    __slots__ = ("buddy_requests", "buddy_messages", "ml_messages", "hq_messages", "blog_posts", "newsletter",
                 "home_region_events", "writing_reminders")

    def __init__(self, data):
        self.buddy_requests = data["email-buddy-requests"]
        self.buddy_messages = data["email-nanomessages-buddies"]
        self.ml_messages = data["email-nanomessages-mls"]
        self.hq_messages = data["email-nanomessages-hq"]
        self.blog_posts = data["email-blog-posts"]
        self.newsletter = data["email-newsletter"]
        self.home_region_events = data["email-events-in-home-region"]
        self.writing_reminders = data["email-writing-reminders"]


class UserStats(Subdata):

    __slots__ = ("projects", "projects_enabled", "streak", "streak_enabled", "word_count", "word_count_enabled",
                 "wordiest", "wordiest_enabled", "writing_pace", "writing_pace_enabled", "years_done", "years_won",
                 "years_enabled")

    def __init__(self, data):
        self.projects = data["stats-projects"]
        self.projects_enabled = data["stats-projects-enabled"]
        self.streak = data["stats-streak"]
        self.streak_enabled = data["stats-streak-enabled"]
        self.word_count = data["stats-word-count"]
        self.word_count_enabled = data["stats-word-count-enabled"]
        self.wordiest = data["stats-wordiest"]
        self.wordiest_enabled = data["stats-wordiest-enabled"]
        self.writing_pace = data["stats-writing-pace"]
        self.writing_pace_enabled = data["stats-writing-pace-enabled"]
        self.years_done = data["stats-years-done"]
        self.years_won = data["stats-years-won"]
        self.years_enabled = data["stats-years-enabled"]


class Funds:

    __slots__ = ("goal", "raised", "donors")

    def __init__(self, data):
        self.goal = data["goal"]
        self.raised = float(data["raised"])
        self.donors = data["donorCount"]


class NanoUser(NanoObj):

    TYPE = "users"

    name = "name"
    slug = "slug"
    time_zone = "time-zone"
    postal_code = "postal-code"
    bio = "bio"
    created_at: dt.datetime = "created-at"
    email = "email"
    location = "location"
    privacy_settings: typing.Optional[PrivacySettings]
    notification_settings: NotificationSettings
    email_settings: EmailSettings
    stats: UserStats
    halos = "halo"
    laurels = "laurels"
    avatar = "avatar"
    plate = "plate"

    def _from_data(self, data):
        super()._from_data(data)
        self._external_links = None
        self._favorite_books = None
        self._favorite_authors = None
        self._genres = None
        self._project_sessions = None
        self._group_users = None
        self._groups = None
        self._timers = None
        self._nanomessages = None
        self._stopwatches = None
        self._user_badges = None
        self._projects = None
        self._project_challenges = None

    async def get_external_links(self):
        if self._external_links is None:
            self._external_links = await self._state.get_related(self._relationships["external-links"])
        return self._external_links

    async def get_favorite_books(self):
        if self._favorite_books is None:
            self._favorite_books = await self._state.get_related(self._relationships["favorite-books"])
        return self._favorite_books

    async def get_favorite_authors(self):
        if self._favorite_authors is None:
            self._favorite_authors = await self._state.get_related(self._relationships["favorite-authors"])
        return self._favorite_authors

    async def get_genres(self):
        if self._genres is None:
            self._genres = await self._state.get_related(self._relationships["genres"])
        return self._genres

    async def get_project_sessions(self):
        if self._project_sessions is None:
            self._project_sessions = await self._state.get_related(self._relationships["project-sessions"])
        return self._project_sessions

    async def get_group_users(self):
        if self._group_users is None:
            self._group_users = await self._state.get_related(self._relationships["group-users"])
        return self._group_users

    async def get_groups(self):
        if self._groups is None:
            self._groups = await self._state.get_related(self._relationships["groups"])
        return self._groups

    async def get_timers(self):
        if self._timers is None:
            self._timers = await self._state.get_related(self._relationships["timers"])
        return self._timers

    async def get_nanomessages(self):
        if self._nanomessages is None:
            self._nanomessages = await self._state.get_related(self._relationships["nanomessages"])
        return self._nanomessages

    async def get_stopwatches(self):
        if self._stopwatches is None:
            self._stopwatches = await self._state.get_related(self._relationships["stopwatches"])
        return self._stopwatches

    async def get_user_badges(self):
        if self._user_badges is None:
            self._user_badges = await self._state.get_related(self._relationships["user-badges"])

    async def get_projects(self):
        if self._projects is None:
            self._projects = sorted(
                await self._state.get_related(self._relationships["projects"]), key=lambda x: x.created_at
            )
        return self._projects

    async def get_project_challenges(self):
        if self._project_challenges is None:
            self._project_challenges = await self._state.get_related(self._relationships['project-challenges'])
        return self._project_challenges


class NanoProject(NanoObj):

    TYPE = "projects"

    user_id = "user-id"
    title = "title"
    slug = "slug"
    unit_type = "unit-type"
    excerpt = "excerpt"
    created_at: dt.datetime = "created-at"
    summary = "summary"
    pinterest = "pinterest-url"
    playlist = "playlist-url"
    privacy = "privacy"
    primary = "primary"
    status = "status"
    cover = "cover"

    def _from_data(self, data):
        super()._from_data(data)
        self._genres = None
        self._project_challenges = None
        self._project_sessions = None
        self._challenges = None
        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_genres(self):
        if self._genres is None:
            self._genres = await self._state.get_related(self._relationships["genres"])
        return self._genres

    async def get_project_challenges(self):
        if self._project_challenges is None:
            self._project_challenges = await self._state.get_related(self._relationships["project-challenges"])
        return self._project_challenges

    async def get_project_sessions(self):
        if self._project_sessions is None:
            self._project_sessions = await self._state.get_related(self._relationships["project-sessions"])
        return self._project_sessions

    async def get_challenges(self):
        if self._challenges is None:
            self._challenges = await self._state.get_related(self._relationships["challenges"])
        return self._challenges

    async def edit_details(self, *, title=_Null, unit_type=_Null, excerpt=_Null, summary=_Null, pinterest=_Null,
                           playlist=_Null, privacy=_Null, primary=_Null, status=_Null, cover=_Null):

        if title is _Null:
            title = self.title
        if unit_type is _Null:
            unit_type = self.unit_type
        if excerpt is _Null:
            excerpt = self.excerpt
        if summary is _Null:
            summary = self.summary
        if pinterest is _Null:
            pinterest = self.pinterest
        if playlist is _Null:
            playlist = self.playlist
        if privacy is _Null:
            privacy = self.privacy
        if primary is _Null:
            primary = self.primary
        if status is _Null:
            status = self.status
        if cover is _Null:
            cover = self.cover

        data = {
            "user-id": self.user_id,
            "title": title,
            "slug": self.slug,
            "unit-type": unit_type,
            "excerpt": excerpt,
            "created-at": self.created_at,
            "summary": summary,
            "pinterest-url": pinterest,
            "playlist-url": playlist,
            "privacy": privacy,
            "primary": primary,
            "status": status,
            "cover": cover
        }

        await self._state.patch_obj(self, data)
        self._from_data(data)


class NanoFavoriteBook(NanoObj):

    TYPE = "favorite-books"

    title = "title"
    user_id = "user-id"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoFavoriteAuthor(NanoObj):

    TYPE = "favorite-authors"

    name = "name"
    user_id = "user-id"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoUserBadge(NanoObj):

    TYPE = "user-badges"

    badge_id = "badge-id"
    user_id = "user-id"
    project_challenge_id = "project-challenge-id"
    created_at: dt.datetime = "created-at"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None
        self._badge = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_badge(self):
        if self._badge is None:
            self._badge = await self._state.get_badge(self.badge_id)
        return self._badge


class NanoBadge(NanoObj):

    TYPE = "badges"

    title = "title"
    list_order = "list-order"
    suborder = "suborder"
    badge_type = "badge-type"
    adheres_to = "adheres-to"
    description = "description"
    awarded_description = "awarded-description"
    generic_description = "generic-description"
    active = "active"
    unawarded = "unawarded"
    awarded = "awarded"


class NanoGenre(NanoObj):

    TYPE = "genres"

    name = "name"
    user_id = "user-id"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoProjectSession(NanoObj):

    TYPE = "project-sessions"

    start = "start"
    end = "end"
    count = "count"
    how = "how"
    where = "where"
    feeling = "feeling"
    created_at: dt.datetime = "created-at"
    unit_type = "unit-type"  # TODO: Unit Type Enum
    project_id = "project-id"

    def _from_data(self, data):
        super()._from_data(data)
        self._project = None
        self._project_challenge = None

    async def get_project(self):
        if self._project is None:
            self._project = await self._state.get_project(self.project_id)
        return self._project

    async def get_project_challenge(self):
        if self._project_challenge is None:
            self._project_challenge = await self._state.get_related(self._relationships["project-challenge"])
        return self._project_challenge


class NanoGroup(NanoObj):

    TYPE = "groups"

    name = "name"
    slug = "slug"
    group_type: GroupType = "group-type"
    description = "description"
    longitude = "longitude"
    latitude = "latitude"
    member_count = "member-count"
    user_id = "user-id"
    group_id = "group-id"
    time_zone = "time-zone"
    created_at: dt.datetime = "created-at"
    updated_at: dt.datetime = "updated-at"
    start_dt = "start-dt"
    end_dt = "end-dt"
    approved_by_id = "approved-by-id"
    url = "url"
    plate = "plate"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None
        self._external_links = None
        self._users = None
        self._nanomessages = None
        self._location_groups = None
        self._locations = None

    async def get_user(self):
        if self.user_id is None:
            return None
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_external_links(self):
        if self._external_links is None:
            self._external_links = await self._state.get_related(self._relationships["external-links"])
        return self._external_links

    async def get_users(self):
        if self._users is None:
            self._users = await self._state.get_related(self._relationships["users"])
        return self._users

    async def get_nanomessages(self):
        if self._nanomessages is None:
            self._nanomessages = await self._state.get_related(self._relationships["nanomessages"])
        return self._nanomessages

    async def get_location_groups(self):
        if self._location_groups is None:
            self._location_groups = await self._state.get_related(self._relationships["location-groups"])
        return self._location_groups

    async def get_locations(self):
        if self._locations is None:
            self._locations = await self._state.get_related(self._relationships["locations"])
        return self._locations


class NanoGroupUser(NanoObj):

    TYPE = "group-users"

    created_at: dt.datetime = "created-at"
    updated_at: dt.datetime = "updated-at"
    group_code_id = "group-code-id"
    is_admin = "is-admin"
    invited_by_id = "invited-by-id"
    invitation_accepted = "invitation-accepted"
    group_id = "group-id"
    user_id = "user-id"
    primary = "primary"
    joined_at = "entry-at"
    join_method: EntryMethod = "entry-method"
    left_at = "exit-at"
    left_method = "exit-method"  # TODO: Exit method enum
    group_type: GroupType = "group-type"
    unread_messages = "num-unread-messages"

    def _from_data(self, data):
        super()._from_data(data)
        self._group = None
        self._user = None
        self._inviter = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_group(self):
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group

    async def get_inviter(self):
        if self.invited_by_id is None:
            return None
        if self._inviter is None:
            self._inviter = await self._state.get_user(self.invited_by_id)
        return self._inviter


class NanoProjectChallenge(NanoObj):

    TYPE = "project-challenges"

    project_id = "project-id"
    starts_at: dt.date = "starts-at"
    ends_at: dt.date = "ends-at"
    challenge_id = "challenge-id"
    start_count = "start-count"
    current_count = "current-count"
    goal = "goal"
    unit_type = "unit-type"  # TODO: Unit type enum
    name = "name"
    nano_event = "nano-event"
    latest_count = "latest-count"

    def _from_data(self, data):
        super()._from_data(data)
        self._project = None
        self._challenge = None
        self._project_sessions = None
        self._user_badges = None

    async def get_project(self):
        if self._project is None:
            self._project = await self._state.get_project(self.project_id)
        return self._project

    async def get_challenge(self):
        if self._challenge is None:
            self._challenge = await self._state.get_challenge(self.challenge_id)
        return self._challenge

    async def get_project_sessions(self):
        if self._project_sessions is None:
            self._project_sessions = await self._state.get_related(self._relationships["project-sessions"])
        return self._project_sessions

    async def get_user_badges(self):
        if self._user_badges is None:
            self._user_badges = await self._state.get_related(self._relationships["user-badges"])
        return self._user_badges

    async def get_stats(self):
        raise NotImplementedError()
        # return await self._state.get_obj(NanoStats, "/daily-aggregates/")


class NanoChallenge(NanoObj):

    TYPE = "challenges"

    event_type: EventType = "event-type"
    start: dt.date = "starts-at"
    end: dt.date = "ends-at"
    unit_type = "unit-type"  # TODO: Unit type enum
    default_goal = "default-goal"
    flexible_goal = "flexible-goal"
    writing_type = "writing-type"  # TODO: Writing type enum
    user_id = "user-id"
    name = "name"
    win_starts: dt.date = "win-allowed-at"
    prep_starts: typing.Optional[dt.date] = "prep-starts-at"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None

    async def get_user(self):
        if not self.user_id:
            return None
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoMessage(NanoObj):

    TYPE = "nanomessages"

    user_id = "user-id"
    group_id = "group-id"
    content = "content"
    created_at: dt.datetime = "created-at"
    updated_at: dt.datetime = "updated-at"
    official = "official"
    avatar_url = "sender-avatar-url"
    sender_name = "sender-name"
    sender_slug = "sender-slug"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None
        self._group = None

    async def get_user(self):
        if self._user is None:
            self._users = await self._state.get_user(self.user_id)
        return self._user

    async def get_group(self):
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group


class NanoExternalLink(NanoObj):

    TYPE = "external-links"

    url = "url"
    user_id = "user-id"

    def _from_data(self, data):
        super()._from_data(data)
        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoGroupExternalLink(NanoObj):

    TYPE = "group-external-links"

    url = "url"
    group_id = "group-id"

    def _from_data(self, data):
        super()._from_data(data)
        self._group = None

    async def get_group(self):
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group


class NanoLocation(NanoObj):

    TYPE = "locations"

    name = "name"
    street1 = "street1"
    street2 = "street2"
    city = "city"
    state = "state"
    country = "country"
    postal_code = "postal-code"
    longitude = "longitude"
    latitude = "latitude"
    formatted_address = "formatted-address"
    map_url = "map-url"
    county = "county"
    neighborhood = "neighborhood"
    municipality = "municipality"
    utc_offset: dt.timezone = "utc-offset"


class NanoLocationGroup(NanoObj):

    TYPE = "location-groups"

    location_id = "location-id"
    group_id = "group-id"
    primary = "primary"

    def _from_data(self, data):
        super()._from_data(data)
        self._location = None
        self._group = None

    async def get_location(self):
        if self._location is None:
            self._location = await self._state.get_location(self.location_id)
        return self._location

    async def get_group(self):
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group
