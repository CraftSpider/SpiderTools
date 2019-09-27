
import datetime as dt
import enum


def _from_iso(s):
    if s[-1] == "Z":
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


class NanoObj:

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

    def _from_data(self, data):
        raise NotImplementedError("Subclasses expected to implement this")

    async def update(self):
        await self._state.update(self)


class PrivacyOptions(enum.IntEnum):
    ANYONE = 2
    BUDDIES = 1
    PRIVATE = 0


class PrivacySettings:

    __slots__ = ("view_buddies", "view_projects", "view_profile", "view_search", "send_messages", "visibility_regions",
                 "visibility_buddies", "visibility_activity")

    def __init__(self, data):
        self.view_buddies = data["privacy-view-buddies"]
        self.view_projects = data["privacy-view-projects"]
        self.view_profile = data["privacy-view-profile"]
        self.view_search = data["privacy-view-search"]
        self.send_messages = data["privacy-send-nanomessages"]
        self.visibility_regions = data["privacy-visibility-regions"]
        self.visibility_buddies = data["privacy-visibility-buddy-lists"]
        self.visibility_activity = data["privacy-visibility-activity-logs"]


class NotificationSettings:

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


class EmailSettings:

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


class UserStats:

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

    def _from_data(self, data):
        self.name = data["name"]
        self.slug = data["slug"]
        self.time_zone = data["time-zone"]
        self.postal_code = data["postal-code"]
        self.bio = data["bio"]
        self.created_at = _from_iso(data["created-at"])
        self.email = data["email"]
        self.location = data["location"]
        try:
            self.privacy_settings = PrivacySettings(data)
        except KeyError:
            self.privacy_settings = None
        try:
            self.notification_settings = NotificationSettings(data)
        except KeyError:
            self.notification_settings = None
        try:
            self.email_settings = EmailSettings(data)
        except KeyError:
            self.email_settings = None
        self.stats = UserStats(data)
        self.halo = data["halo"]
        self.laurels = data["laurels"]
        self.avatar = data["avatar"]
        self.plate = data["plate"]

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

    def _from_data(self, data):
        self.user_id = data["user-id"]
        self.title = data["title"]
        self.slug = data["slug"]
        self.unit_type = data["unit-type"]
        self.excerpt = data["excerpt"]
        self.created_at = _from_iso(data["created-at"])
        self.summary = data["summary"]
        self.pinterest = data["pinterest-url"]
        self.playlist = data["playlist-url"]
        self.privacy = data["privacy"]
        self.primary = data["primary"]
        self.status = data["status"]
        self.cover = data["cover"]

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


class NanoFavoriteBook(NanoObj):

    TYPE = "favorite-books"

    def _from_data(self, data):
        self.title = data["title"]
        self.user_id = data["user-id"]

        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoFavoriteAuthor(NanoObj):

    TYPE = "favorite-authors"

    def _from_data(self, data):
        self.name = data["name"]
        self.user_id = data["user-id"]

        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoUserBadge(NanoObj):

    TYPE = "user-badges"

    def _from_data(self, data):
        self.badge_id = data["badge-id"]
        self.user_id = data["user-id"]
        self.project_challenge_id = data["project-challenge-id"]
        self.created_at = _from_iso(data["created-at"])

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

    def _from_data(self, data):
        self.title = data["title"]
        self.list_order = data["list-order"]
        self.suborder = data["suborder"]
        self.badge_type = data["badge-type"]
        self.adheres_to = data["adheres-to"]
        self.description = data["description"]
        self.awarded_description = data["awarded-description"]
        self.generic_description = data["generic-description"]
        self.active = data["active"]
        self.unawarded = data["unawarded"]
        self.awarded = data["awarded"]


class NanoGenre(NanoObj):

    TYPE = "genres"

    def _from_data(self, data):
        self.name = data["name"]
        self.user_id = data["user-id"]

        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoProjectSession(NanoObj):

    TYPE = "project-sessions"

    def _from_data(self, data):
        self.start = data["start"]
        self.end = data["end"]
        self.count = data["count"]
        self.how = data["how"]
        self.where = data["where"]
        self.feeling = data["feeling"]
        self.created_at = _from_iso(data["created-at"])
        self.unit_type = data["unit-type"]
        self.project_id = data["project-id"]

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

    def _from_data(self, data):
        self.name = data["name"]
        self.slug = data["slug"]
        self.group_type = data["group-type"]  # TODO: Group type enum
        self.description = data["description"]
        self.longitude = data["longitude"]
        self.latitude = data["latitude"]
        self.member_count = data["member-count"]
        self.user_id = data["user_id"]
        self.group_id = data["group_id"]
        self.time_zone = data["time_zone"]
        self.created_at = _from_iso(data["created-at"])
        self.updated_at = _from_iso(data["updated-at"])
        self.start_dt = data["start_dt"]
        self.end_dt = data["end-dt"]
        self.approved_by_id = data["approved-by-id"]
        self.url = data["url"]
        self.plate = data["plate"]

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

    def _from_data(self, data):
        self.created_at = _from_iso(data["created-at"])
        self.updated_at = _from_iso(data["updated-at"])
        self.group_code_id = data["group-code-id"]
        self.is_admin = data["is-admin"]
        self.invited_by_id = data["invited-by-id"]
        self.invitation_accepted = data["invitation-accepted"]
        self.group_id = data["group-id"]
        self.user_id = data["user_id"]
        self.primary = data["primary"]
        self.joined_at = data["entry-at"]
        self.join_method = data["entry-method"]
        self.left_at = data["exit-at"]
        self.left_method = data["exit-method"]
        self.group_type = data["group-type"]  # TODO: Group type enum
        self.unread_messages = data["num-unread-messages"]

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

    def _from_data(self, data):
        self.project_id = data["project-id"]
        self.starts_at = data["starts-at"]
        self.ends_at = data["ends-at"]
        self.challenge_id = data["challenge-id"]
        self.start_count = data["start-count"]
        self.current_count = data["current-count"]
        self.goal = data["goal"]
        self.unit_type = data["unit-type"]
        self.name = data["name"]
        self.nano_event = data["nano-event"]
        self.latest_count = data["latest-count"]

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


class NanoChallenge(NanoObj):

    TYPE = "challenges"

    def _from_data(self, data):
        self.event_type = data["event-type"]  # TODO: Event type enum
        self.start = data["starts-at"]
        self.end = data["ends-at"]
        self.unit_type = data["unit-type"]
        self.default_goal = data["default-goal"]
        self.flexible_goal = data["flexible-goal"]
        self.writing_type = data["writing-type"]  # TODO: Writing type enum
        self.user_id = data["user-id"]
        self.name = data["name"]
        self.win_starts = data["win-allowed-at"]
        self.prep_starts = data["prep-starts-at"]

        self._user = None

    async def get_user(self):
        if not self.user_id:
            return None
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoMessage(NanoObj):

    TYPE = "nanomessages"

    def _from_data(self, data):
        self.user_id = data["user-id"]
        self.group_id = data["group-id"]
        self.content = data["content"]
        self.created_at = _from_iso(data["created-at"])
        self.updated_at = _from_iso(data["updated-at"])
        self.official = data["official"]
        self.avatar_url = data["sender-avatar-url"]
        self.sender_name = data["sender-name"]
        self.sender_slug = data["sender-slug"]

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

    def _from_data(self, data):
        self.url = data["url"]
        self.user_id = data["user-id"]

        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


class NanoGroupExternalLink(NanoObj):

    TYPE = "group-external-links"

    def _from_data(self, data):
        self.url = data["url"]
        self.group_id = data["group-id"]

        self._group = None

    async def get_group(self):
        if self._group is None:
            self._group = await self._state.get_group(self.group_id)
        return self._group


class NanoLocation(NanoObj):

    TYPE = "locations"

    def _from_data(self, data):
        self.name = data["name"]
        self.street1 = data["street1"]
        self.street2 = data["street2"]
        self.city = data["city"]
        self.state = data["state"]
        self.country = data["country"]
        self.postal_code = data["postal-code"]
        self.longitude = data["longitude"]
        self.latitude = data["latitude"]
        self.formatted_address = data["formatted-address"]
        self.map_url = data["map-url"]
        self.county = data["county"]
        self.neighborhood = data["neighborhood"]
        self.municipality = data["municipality"]
        self.utc_offset = data["utc-offset"]


class NanoLocationGroup(NanoObj):

    TYPE = "location-groups"

    def _from_data(self, data):
        self.location_id = data["location-id"]
        self.group_id = data["group-id"]
        self.primary = data["primary"]

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
