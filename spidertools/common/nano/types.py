
import typing
import datetime as dt
from .enums import *


def _from_iso(s):
    """
        Convert an ISO string to a datetime object, with Z extension supported
    :param s: String to convert
    :return: Datetime object of string
    """
    if s[-1] == "Z":
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def _from_date(s):
    """
        Convert a string in the common Nano date format to a date object
    :param s: String to convert
    :return: Date object of string
    """
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def _from_tz(s):
    """
        Return a timezone with a given number of minutes offset
    :param s: Offset in minutes
    :return: Timezone with given offset
    """
    return dt.timezone(dt.timedelta(minutes=s))


def _is_dunder(s):
    """
        Whether a given name is a dunder name
    :param s: Name to check
    :return: Whether name is dunder
    """
    return s.startswith("__") and s.endswith("__")


def _get_convert(cls):
    """
        Get the conversion function to use with a given type annotation
    :param cls: Type annotation on object
    :return: Converter function to use
    """
    if cls == dt.datetime:
        return _from_iso
    elif cls == dt.date:
        return _from_date
    elif cls == dt.timezone:
        return _from_tz
    else:
        return cls


_Null = object()


class NanoMeta(type):
    """
        Metaclass for all Nano Objects. Handles conversion from annotations into attribute data for
        automatic conversion to/from JSON
    """

    def __new__(mcs, name, bases, namespace):
        """
            Create a new class with this metaclass. Reads annotations and generates relevant type data
        :param name: New class name
        :param bases: New class subclasses
        :param namespace: New class namespace
        """
        new_namespace = {
            "_ATTR_DATA": {},
            "LINKS": ()
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
    """
        Class that represents API objects for the Nano framework
        Associated with a state, other objects, and an ID
    """

    __slots__ = ("_state", "_relationships", "_self", "id")

    TYPE_MAP = {}

    def __init__(self, state, data):
        """
            Prepare a new object from raw API data
        :param state: Associated state
        :param data: JSON data from the API
        """
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
        """
            Create Nano object subclasses. Verifies that they have a TYPE member, and
            registers them with the map of type names to types
        :param kwargs: Keyword arguments to class
        """
        if not hasattr(cls, "TYPE"):
            raise TypeError("NanoObj subclasses must provide a TYPE")
        NanoObj.TYPE_MAP[cls.TYPE] = cls

    def _do_convert(self, cls, name, data):
        """
            Handles conversion from JSON data to a class object
        :param cls: Class to convert to
        :param name: Name of the data in JSON
        :param data: JSON data for object
        :return: Converted value
        """
        func = _get_convert(cls)
        if isinstance(func, type) and issubclass(func, Subdata):
            val = func(data)
        elif isinstance(func, typing._GenericAlias):
            val = self._generic_convert(func, name, data)
        else:
            val = data.get(name, _Null)
            if val is _Null:
                raise AttributeError(f"Data for {self.__class__.__name__} doesn't contain attribute {name}")
            val = func(val)
        return val

    def _generic_convert(self, cls, name, data):
        """
            Handle conversion of an object that may be a union of types
        :param cls: Class to convert to
        :param name: Name of the data in JSON
        :param data: JSON data for object
        :return: Converted value
        """
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
        """
            Populate this object from JSON data
        :param data: JSON data for object
        """
        for name, attr in self._ATTR_DATA.items():
            val = self._do_convert(attr[0], attr[1], data)
            setattr(self, name, val)
        for name in self.LINKS:
            setattr(self, f"_{name.replace('-', '_')}", None)

    def _to_json(self, cls, val, data):  # TODO: Handle complex types
        """
            Convert an attribute of this object into JSON data
        :param cls: Class to convert from
        :param val: Value to convert
        :param data: Output dict
        :return: Converted value
        """
        if isinstance(val, Subdata):
            data.update(val._to_data())
            return _Null
        return val

    def _to_data(self):
        """
            Convert this object into a dict of JSON data
        :return: JSON compliant dict
        """
        out = {}
        for name, attr in self._ATTR_DATA.items():
            val = getattr(self, name)
            val = self._to_json(attr[0], val, out)
            if val is not _Null:
                out[attr[1]] = val
        return out

    async def edit(self, **kwargs):
        """
            Alter this object, and patch it on the API
        :param kwargs: Attributes to alter
        """
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
        """
            Update this object from the API
        """
        await self._state.update(self)


class Subdata:
    """
        Class representing sub-objects of a Nano object, a dict that doesn't necessarily have its own
        ID or state
    """

    def _to_data(self):
        """
            Convert subdata to its JSON representation
        :return: Dictionary of subdata values
        """
        raise NotImplementedError()


class PrivacySettings(Subdata):
    """
        User privacy settings. Consists of various info about who is allowed to see what user info
    """

    __slots__ = ("view_buddies", "view_projects", "view_profile", "view_search", "send_messages", "visibility_regions",
                 "visibility_buddies", "visibility_activity")

    def __init__(self, data):
        """
            Create new PrivacySettings instance from user data
        :param data: User data to set values from
        """
        self.view_buddies = PrivacyOptions(data["privacy-view-buddies"])
        self.view_projects = PrivacyOptions(data["privacy-view-projects"])
        self.view_profile = PrivacyOptions(data["privacy-view-profile"])
        self.view_search = PrivacyOptions(data["privacy-view-search"])
        self.send_messages = PrivacyOptions(data["privacy-send-nanomessages"])
        self.visibility_regions = data["privacy-visibility-regions"]
        self.visibility_buddies = data["privacy-visibility-buddy-lists"]
        self.visibility_activity = data["privacy-visibility-activity-logs"]

    def _to_data(self):
        """
            Convert PrivacySettings to its JSON representation
        :return: Dictionary of subdata values
        """
        return {
            "privacy-view-buddies": self.view_buddies,
            "privacy-view-projects": self.view_projects,
            "privacy-view-profile": self.view_profile,
            "privacy-view-search": self.view_search,
            "privacy-send-nanomessages": self.send_messages,
            "privacy-visibility-regions": self.visibility_regions,
            "privacy-visibility-buddy-lists": self.visibility_buddies,
            "privacy-visibility-activity-logs": self.visibility_activity
        }


class NotificationSettings(Subdata):
    """
        User notification settings. Consists of various info about what notifications the user receives
    """

    __slots__ = ("buddy_requests", "buddy_activities", "buddy_messages", "ml_messages", "hq_messages",
                 "sprint_invitation", "sprint_start", "writing_reminders", "goal_milestones", "home_region_events",
                 "new_badges")

    def __init__(self, data):
        """
            Create a new NotificationSettings instance from user data
        :param data: User data to set values from
        """
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

    def _to_data(self):
        """
            Convert NotificationSettings to its JSON representation
        :return: Dictionary of subdata values
        """
        return {
            "notification-buddy-requests": self.buddy_requests,
            "notification-buddy-activities": self.buddy_activities,
            "notification-nanomessages-buddies": self.buddy_messages,
            "notification-nanomessages-mls": self.ml_messages,
            "notification-nanomessages-hq": self.hq_messages,
            "notification-sprint-invitation": self.sprint_invitation,
            "notification-sprint-start": self.sprint_start,
            "notification-writing-reminders": self.writing_reminders,
            "notification-goal-milestones": self.goal_milestones,
            "notification-events-in-home-region": self.home_region_events,
            "notification-new-badges": self.new_badges
        }


class EmailSettings(Subdata):
    """
        User email settings. Consists of various info about what emails a user receives
    """

    __slots__ = ("buddy_requests", "buddy_messages", "ml_messages", "hq_messages", "blog_posts", "newsletter",
                 "home_region_events", "writing_reminders")

    def __init__(self, data):
        """
            Create a new EmailSettings instance from user data
        :param data: User data to set values from
        """
        self.buddy_requests = data["email-buddy-requests"]
        self.buddy_messages = data["email-nanomessages-buddies"]
        self.ml_messages = data["email-nanomessages-mls"]
        self.hq_messages = data["email-nanomessages-hq"]
        self.blog_posts = data["email-blog-posts"]
        self.newsletter = data["email-newsletter"]
        self.home_region_events = data["email-events-in-home-region"]
        self.writing_reminders = data["email-writing-reminders"]


class UserStats(Subdata):
    """
        User current stats. Consists of various info about a user's global statistics
    """

    __slots__ = ("projects", "projects_enabled", "streak", "streak_enabled", "word_count", "word_count_enabled",
                 "wordiest", "wordiest_enabled", "writing_pace", "writing_pace_enabled", "years_done", "years_won",
                 "years_enabled")

    def __init__(self, data):
        """
            Create a new UserStats instance from user data
        :param data: User data to set values from
        """
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
    """
        The state of the Nano fundometer
    """

    __slots__ = ("goal", "raised", "donors")

    def __init__(self, data):
        """
            Create a new Fundometer instance from JSON data
        :param data: JSON data about fundometer
        """
        self.goal = data["goal"]
        self.raised = float(data["raised"])
        self.donors = data["donorCount"]


class NanoUser(NanoObj):
    """
        Represents a user on the Nano site
    """

    TYPE = "users"
    LINKS = [
        "external-links",
        "favorite-books",
        "favorite-authors",
        "genres",
        "project-sessions",
        "group-users",
        "groups",
        "timers",
        "nanomessages",
        "stopwatches",
        "user-badges",
        "projects",
        "project-challenges"
    ]

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

    async def get_external_links(self):
        """
            Get the external links associated with this user
        :return: List of external links
        """
        if self._external_links is None:
            self._external_links = await self._state.get_related(self._relationships["external-links"])
        return self._external_links

    async def get_favorite_books(self):
        """
            Get the favorite books associated with this user
        :return: List of favorite books
        """
        if self._favorite_books is None:
            self._favorite_books = await self._state.get_related(self._relationships["favorite-books"])
        return self._favorite_books

    async def get_favorite_authors(self):
        """
            Get the favorite authors associated with this user
        :return: List of favorite authors
        """
        if self._favorite_authors is None:
            self._favorite_authors = await self._state.get_related(self._relationships["favorite-authors"])
        return self._favorite_authors

    async def get_genres(self):
        """
            Get the genres associated with this user
        :return: List of genres
        """
        if self._genres is None:
            self._genres = await self._state.get_related(self._relationships["genres"])
        return self._genres

    async def get_project_sessions(self):
        """
            Get the project sessions associated with this user
        :return: List of project sessions
        """
        if self._project_sessions is None:
            self._project_sessions = await self._state.get_related(self._relationships["project-sessions"])
        return self._project_sessions

    async def get_group_users(self):
        """
            Get the group users associated with this user
        :return: List of group users
        """
        if self._group_users is None:
            self._group_users = await self._state.get_related(self._relationships["group-users"])
        return self._group_users

    async def get_groups(self):
        """
            Get the groups associated with this uesr
        :return: List of groups
        """
        if self._groups is None:
            self._groups = await self._state.get_related(self._relationships["groups"])
        return self._groups

    async def get_timers(self):
        """
            Get the timers associated with this user
        :return: List of timers
        """
        if self._timers is None:
            self._timers = await self._state.get_related(self._relationships["timers"])
        return self._timers

    async def get_nanomessages(self):
        """
            Get the nanomessages associated with this user
        :return: List of nanomessages
        """
        if self._nanomessages is None:
            self._nanomessages = await self._state.get_related(self._relationships["nanomessages"])
        return self._nanomessages

    async def get_stopwatches(self):
        """
            Get the stopwatches associated with this user
        :return: List of stopwatches
        """
        if self._stopwatches is None:
            self._stopwatches = await self._state.get_related(self._relationships["stopwatches"])
        return self._stopwatches

    async def get_user_badges(self):
        """
            Get the user badges associated with this user
        :return: List of user badges
        """
        if self._user_badges is None:
            self._user_badges = await self._state.get_related(self._relationships["user-badges"])

    async def get_projects(self):
        """
            Get the projects associated with this user
        :return: List of projects
        """
        if self._projects is None:
            self._projects = sorted(
                await self._state.get_related(self._relationships["projects"]), key=lambda x: x.created_at
            )
        return self._projects

    async def get_project_challenges(self):
        """
            Get the project challenges associated with this user
        :return: List of project challenges
        """
        if self._project_challenges is None:
            self._project_challenges = await self._state.get_related(self._relationships['project-challenges'])
        return self._project_challenges


class NanoProject(NanoObj):
    """
        Represents a project on the Nano site
    """

    TYPE = "projects"
    LINKS = [
        "user",
        "genres",
        "project-challenges",
        "project-sessions",
        "challenges"
    ]

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

    async def get_user(self):
        """
            Get the user associated with this project
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_genres(self):
        """
            Get the genres associated with this project
        :return: List of genres
        """
        if self._genres is None:
            self._genres = await self._state.get_related(self._relationships["genres"])
        return self._genres

    async def get_project_challenges(self):
        """
            Get the project challenges associated with this project
        :return: List of project challenges
        """
        if self._project_challenges is None:
            self._project_challenges = await self._state.get_related(self._relationships["project-challenges"])
        return self._project_challenges

    async def get_project_sessions(self):
        """
            Get the project sessions associated with this project
        :return: List of project sessions
        """
        if self._project_sessions is None:
            self._project_sessions = await self._state.get_related(self._relationships["project-sessions"])
        return self._project_sessions

    async def get_challenges(self):
        """
            Get the challenges associated with this project
        :return: List of challenges
        """
        if self._challenges is None:
            self._challenges = await self._state.get_related(self._relationships["challenges"])
        return self._challenges

    async def edit_details(self, *, title=_Null, unit_type=_Null, excerpt=_Null, summary=_Null, pinterest=_Null,
                           playlist=_Null, privacy=_Null, primary=_Null, status=_Null, cover=_Null):
        """
            Edit this project, only provided values are altered
        :param title: Project title
        :param unit_type: Unit type
        :param excerpt: Excerpt string
        :param summary: Summary string
        :param pinterest: Pinterest board link
        :param playlist: Spotify playlist link
        :param privacy: Privacy settings
        :param primary: Whether the project is the primary project
        :param status: The project status
        :param cover: Project cover image link
        """

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
    """
        Represents a user's favorite book on the Nano site
    """

    TYPE = "favorite-books"
    LINKS = [
        "user"
    ]

    title = "title"
    user_id = "user-id"

    async def get_user(self):
        """
            Get the user associated with this favorite book
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoFavoriteAuthor(NanoObj):
    """
        Represents a user's favorite author on the Nano site
    """

    TYPE = "favorite-authors"
    LINKS = [
        "user"
    ]

    name = "name"
    user_id = "user-id"

    async def get_user(self):
        """
            Get the user associated with this favorite author
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoUserBadge(NanoObj):
    """
        Represents a user owned badge on the Nano site
    """

    TYPE = "user-badges"
    LINKS = [
        "user",
        "badge"
    ]

    badge_id = "badge-id"
    user_id = "user-id"
    project_challenge_id = "project-challenge-id"
    created_at: dt.datetime = "created-at"

    async def get_user(self):
        """
            Get the user associated with this user badge
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_badge(self):
        """
            Get the badge associated with this user badge
        :return: Single badge
        """
        if self._badge is None:
            self._badge = await self._state.get_badge(self.badge_id)
        return self._badge


class NanoBadge(NanoObj):
    """
        Represents a badge on the Nano site
    """

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
    """
        Represents a book genre on the Nano site
    """

    TYPE = "genres"
    LINKS = [
        "user"
    ]

    name = "name"
    user_id = "user-id"

    async def get_user(self):
        """
            Get the user associated with this genre
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoProjectSession(NanoObj):
    """
        Represents a project session on the Nano site
    """

    TYPE = "project-sessions"
    LINKS = [
        "project",
        "project-challenge"
    ]

    start = "start"
    end = "end"
    count = "count"
    how = "how"
    where = "where"
    feeling = "feeling"
    created_at: dt.datetime = "created-at"
    unit_type = "unit-type"  # TODO: Unit Type Enum
    project_id = "project-id"

    async def get_project(self):
        """
            Get the project associated with this project session
        :return: Single project
        """
        if self._project is None:
            self._project = await self._state.get_project(self.project_id)
        return self._project

    async def get_project_challenge(self):
        """
            Get the project challenge associated with this project session
        :return: Single project challenge
        """
        if self._project_challenge is None:
            self._project_challenge = await self._state.get_related(self._relationships["project-challenge"])
        return self._project_challenge


class NanoGroup(NanoObj):
    """
        Represents a group on the Nano site
    """

    TYPE = "groups"
    LINKS = [
        "user",
        "external-links",
        "users",
        "nanomessages",
        "location-groups",
        "locations"
    ]

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

    async def get_user(self):
        """
            Get the user associated with this group
        :return: Single user
        """
        if self.user_id is None:
            return None
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_external_links(self):
        """
            Get the external links associated with this group
        :return: List of external links
        """
        if self._external_links is None:
            self._external_links = await self._state.get_related(self._relationships["external-links"])
        return self._external_links

    async def get_users(self):
        """
            Get the users associated with this group
        :return: List of users
        """
        if self._users is None:
            self._users = await self._state.get_related(self._relationships["users"])
        return self._users

    async def get_nanomessages(self):
        """
            Get the nanomessages associated with this group
        :return: List of nanomessages
        """
        if self._nanomessages is None:
            self._nanomessages = await self._state.get_related(self._relationships["nanomessages"])
        return self._nanomessages

    async def get_location_groups(self):
        """
            Get the location groups associated with this group
        :return: List of location groups
        """
        if self._location_groups is None:
            self._location_groups = await self._state.get_related(self._relationships["location-groups"])
        return self._location_groups

    async def get_locations(self):
        """
            Get the locations associated with this group
        :return: List of locations
        """
        if self._locations is None:
            self._locations = await self._state.get_related(self._relationships["locations"])
        return self._locations


class NanoGroupUser(NanoObj):
    """
        Represents a user's membership in a group on the Nano site
    """

    TYPE = "group-users"
    LINKS = [
        "group",
        "user",
        "inviter"
    ]

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

    async def get_user(self):
        """
            Get the user associated with this group user
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_group(self):
        """
            Get the group associated with this group user
        :return: Single group
        """
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group

    async def get_inviter(self):
        """
            Get the inviter associated with this group user
        :return: Single user
        """
        if self.invited_by_id is None:
            return None
        if self._inviter is None:
            self._inviter = await self._state.get_user(self.invited_by_id)
        return self._inviter


class NanoProjectChallenge(NanoObj):
    """
        Represents a project and challenge link on the Nano site
    """

    TYPE = "project-challenges"
    LINKS = [
        "project",
        "challenge",
        "project-sessions",
        "user-badges"
    ]

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

    async def get_project(self):
        """
            Get the project associated with this project challenge
        :return: Single project
        """
        if self._project is None:
            self._project = await self._state.get_project(self.project_id)
        return self._project

    async def get_challenge(self):
        """
            Get the challenge associated with this project challenge
        :return: Single challenge
        """
        if self._challenge is None:
            self._challenge = await self._state.get_challenge(self.challenge_id)
        return self._challenge

    async def get_project_sessions(self):
        """
            Get the project sessions associated with this project challenge
        :return: List of project sessions
        """
        if self._project_sessions is None:
            self._project_sessions = await self._state.get_related(self._relationships["project-sessions"])
        return self._project_sessions

    async def get_user_badges(self):
        """
            Get the user badges associated with this project challenge
        :return: List of user badges
        """
        if self._user_badges is None:
            self._user_badges = await self._state.get_related(self._relationships["user-badges"])
        return self._user_badges

    async def get_stats(self):
        """
            Get the stats associated with this project challenge. Doesn't function correctly yet
        """
        raise NotImplementedError()
        # return await self._state.get_obj(NanoStats, "/daily-aggregates/")


class NanoChallenge(NanoObj):
    """
        Represents a challenge on the Nano site
    """

    TYPE = "challenges"
    LINKS = [
        "user"
    ]

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

    async def get_user(self):
        """
            Get the user associated with this challenge
        :return: Single user
        """
        if not self.user_id:
            return None
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoMessage(NanoObj):
    """
        Represents a private message on the Nano site
    """

    TYPE = "nanomessages"
    LINKS = [
        "user",
        "group"
    ]

    user_id = "user-id"
    group_id = "group-id"
    content = "content"
    created_at: dt.datetime = "created-at"
    updated_at: dt.datetime = "updated-at"
    official = "official"
    avatar_url = "sender-avatar-url"
    sender_name = "sender-name"
    sender_slug = "sender-slug"

    async def get_user(self):
        """
            Get the user associated with this nanomessage
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user

    async def get_group(self):
        """
            Get the group associated with this nanomessage
        :return: Single group
        """
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group


class NanoExternalLink(NanoObj):
    """
        Represents an external link on the Nano site
    """

    TYPE = "external-links"
    LINKS = [
        "user"
    ]

    url = "url"
    user_id = "user-id"

    async def get_user(self):
        """
            Get the user associated with this external link
        :return: Single user
        """
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoGroupExternalLink(NanoObj):
    """
        Represents a group's external link on the Nano site
    """

    TYPE = "group-external-links"
    LINKS = [
        "group"
    ]

    url = "url"
    group_id = "group-id"

    async def get_group(self):
        """
            Get the group associated with this external link
        :return: Single group
        """
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group


class NanoLocation(NanoObj):
    """
        Represents a location on the Nano site
    """

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
    """
        Represents a group's location on the Nano site
    """

    TYPE = "location-groups"
    LINKS = [
        "location",
        "group"
    ]

    location_id = "location-id"
    group_id = "group-id"
    primary = "primary"

    async def get_location(self):
        """
            Get the location associated with this location group
        :return: Single location
        """
        if self._location is None:
            self._location = await self._state.get_location(self.location_id)
        return self._location

    async def get_group(self):
        """
            Get the group associated with this location group
        :return: Single group
        """
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group
