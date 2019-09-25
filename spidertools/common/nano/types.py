
import enum


class NanoObj:

    __slots__ = ("_state", "_relationships", "id")

    TYPE_MAP = {}

    def __init__(self, state, data):
        self._state = state
        self.id = int(data["id"])
        self._relationships = {x: data["relationships"][x]["links"]["related"] for x in data["relationships"]}
        self._from_data(data["attributes"])

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "TYPE"):
            raise TypeError("NanoObj subclasses must provide a TYPE")
        NanoObj.TYPE_MAP[cls.TYPE] = cls

    def _from_data(self, data):
        raise NotImplementedError("Subclasses expected to implement this")


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


class NanoUser(NanoObj):

    TYPE = "users"

    def _from_data(self, data):
        self.name = data["name"]
        self.slug = data["slug"]
        self.time_zone = data["time-zone"]
        self.postal_code = data["postal-code"]
        self.bio = data["bio"]
        self.created_at = data["created-at"]
        self.email = data["email"]
        self.location = data["location"]
        self.privacy_settings = PrivacySettings(data)
        self.notification_settings = NotificationSettings(data)
        self.email_settings = EmailSettings(data)
        self.halo = data["halo"]
        self.laurels = data["laurels"]
        self.avatar = data["avatar"]
        self.plate = data["plate"]

        # TODO: If being made from included data, add that
        self._external_links = None
        self._projects = None

    async def get_external_links(self):
        if self._external_links is None:
            self._external_links = await self._state.get_related(self._relationships["external-links"])
        return self._external_links

    async def get_favorite_books(self):
        pass

    async def get_favorite_authors(self):
        pass

    async def get_genres(self):
        pass

    async def get_project_sessions(self):
        pass

    async def get_group_users(self):
        pass

    async def get_groups(self):
        pass

    async def get_timers(self):
        pass

    async def get_nanomessages(self):
        pass

    async def get_stopwatches(self):
        pass

    async def get_user_badges(self):
        pass

    async def get_projects(self):
        if self._projects is None:
            self._projects = await self._state.get_related(self._relationships["projects"])
        return self._projects

    async def get_project_challenges(self):
        pass


class NanoExternalLink(NanoObj):

    TYPE = "external-links"

    def _from_data(self, data):
        raise NotImplementedError("External links not yet implemented")


class NanoProject(NanoObj):

    TYPE = "projects"

    def _from_data(self, data):
        self.user_id = data["user-id"]
        self.title = data["title"]
        self.slug = data["slug"]
        self.unit_type = data["unit-type"]
        self.excerpt = data["excerpt"]
        self.created_at = data["created-at"]
        self.summary = data["summary"]
        self.pinterest = data["pinterest-url"]
        self.playlist = data["playlist-url"]
        self.privacy = data["privacy"]
        self.primary = data["primary"]
        self.status = data["status"]
        self.cover = data["cover"]

        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user


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
        self.user_id = data["user_name"]

        self._user = None

    async def get_user(self):
        if self._user is None:
            self._user = await self._state.get_user(self.user_id)
        return self._user
