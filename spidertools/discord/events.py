
import datetime as dt
import asyncio
import logging
import inspect

from spidertools.common import data, utils
from . import errors


log = logging.getLogger("talos.dutils.events")


def align_period(period):
    """
        Align a period for its next execution. From now, push forward the period, then down to the nearest 0.
    :param period: Period to return alignment for
    :return: delta till when period should next run
    """
    now = dt.datetime.now()
    days = 0
    hours = 0
    minutes = 0
    seconds = 0
    if period.days:
        hours = 24 - now.hour
        minutes = 60 - now.minute
        seconds = 60 - now.second
    elif period.hours:
        minutes = 60 - now.minute
        seconds = 60 - now.second
    elif period.minutes:
        seconds = 60 - now.second

    days += period.days - 1 if period.days else 0
    hours += period.hours - 1 if period.hours else 0
    minutes += period.minutes - 1 if period.minutes else 0
    seconds += period.seconds - 1 if period.seconds else 0

    return dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


class EventPeriod(data.SqlConvertable):
    """
        Represents the period of time used between runs in an EventLoop. Similar to a timedelta, but
        functions slightly differently
    """

    __slots__ = ("_seconds",)

    def __new__(cls, period):
        """
            Create a new EventPeriod. If input is None, then we return None instead of a new
            EventPeriod
        :param period: object to create a new EventPeriod from
        :return: Newly created EventPeriod, or None
        """
        if period is None:
            return None
        else:
            return super().__new__(cls)

    def __init__(self, period):
        """
            Initialize an EventPeriod. If input is an EventPeriod, we create a copy.
            Otherwise we read out a string into our memory.
        :param period: Either EventPeriod to copy, or a string to read
        """
        if isinstance(period, EventPeriod):
            self._seconds = period._seconds
            return
        num = ""
        self._seconds = 0
        for char in period:
            if char == "d" or char == "h" or char == "m" or char == "s":
                if char == "d":
                    self._seconds += int(num) * 86400
                elif char == "h":
                    self._seconds += int(num) * 3600
                elif char == "m":
                    self._seconds += int(num) * 60
                elif char == "s":
                    self._seconds += int(num)
                num = ""
            elif "0" <= char <= "9":
                num += char

    def __str__(self):
        """
            Convert an EventPeriod into its string representation
        :return: String form of EventPeriod
        """
        out = ""
        if self.days:
            out += f"{self.days}d"
        if self.hours:
            out += f"{self.hours}h"
        if self.minutes:
            out += f"{self.minutes}m"
        if self.seconds:
            out += f"{self.seconds}s"
        return out

    def __int__(self):
        """
            Convert to integer representation, the number of seconds in this period in total
        :return: Seconds in EventPeriod
        """
        return self._seconds

    @property
    def days(self):
        """
            Get the number of days in this period
        :return: Number of days in the period
        """
        return self._seconds // 86400

    @property
    def hours(self):
        """
            Get the number of whole hours in this period, minus days
        :return: Number of hours in the period
        """
        return (self._seconds % 86400) // 3600

    @property
    def minutes(self):
        """
            Get the number of whole minutes in this period, minus hours and days
        :return: Number of minutes in this period
        """
        return (self._seconds % 3600) // 60

    @minutes.setter
    def minutes(self, value):
        """
            Set the number of minutes in this period. Should be a number between 0-59
        :param value: Number of minutes to set to
        """
        dif = value - self.minutes
        self._seconds += dif * 60

    @property
    def seconds(self):
        """
            Get the number of whole seconds in this period, minus greater values
        :return: Number of seconds in this period
        """
        return self._seconds % 60

    @seconds.setter
    def seconds(self, value):
        """
            Set the number of seconds in this period. Should be a number between 0-59
        :param value:
        :return:
        """
        dif = value - self.seconds
        self._seconds += dif

    def timedelta(self):
        """
            Get the timedelta representation of this period
        :return: timedelta object matching this period
        """
        return dt.timedelta(seconds=int(self))

    def sql_safe(self):
        """
            Convert this period to a string to store in a SQL database
        :return: String for storage in database
        """
        return str(self)


class EventLoop:
    """
        Conceptually, an event that should be run every X length of time. Takes an asynchronous function,
        and runs it once for every passing of period length of time.
    """

    __slots__ = ("_task", "__wrapped__", "_instance", "period", "persist", "start_time", "loop", "name", "parent",
                 "description", "long_desc")

    def __call__(self, *args, **kwargs):
        """
            An attempt to directly call an EventLoop should fail
        """
        raise NotImplementedError("Access internal method through self.callback")

    def __init__(self, coro, period, loop=None, **kwargs):
        """
            Initialize an eventloop object with a coroutine and period at least
        :param coro: Internal coroutine object
        :param period: Interval between calls
        :param loop: asyncio event loop, if None uses default
        :param kwargs: Other parameters. Description, persist (whether to ignore errors), start_time, and name.
                       If name is not provided, then coro.__name__ is used instead
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        self.__wrapped__ = coro
        self._task = None
        self.description = inspect.cleandoc(kwargs.get("description"))
        self.long_desc = inspect.cleandoc(kwargs.get("long_desc", inspect.getdoc(coro)))
        self.period = EventPeriod(period)
        self.persist = kwargs.get("persist")
        self.start_time = kwargs.get("start_time")
        self.name = kwargs.get("name", coro.__name__)
        self.loop = loop
        self.parent = None

    def __str__(self):
        """
            Convert this eventloop to a string representation, containing the period, name, and short description
        :return: String form of loop
        """
        return f"EventLoop(period: {self.period}, name: {self.name}, description: {self.description})"

    @property
    def callback(self):
        """
            Retrieve the internal callback object
        :return: Internal coro
        """
        return self.__wrapped__

    @callback.setter
    def callback(self, value):
        """
            Set the internal callback object
        :param value: Callback to set
        """
        self.__wrapped__ = value

    def set_start_time(self, time):
        """
            Set the EventLoop start time. While event loop is running, this won't change anything
        :param time: datetime to start the loop at
        :return:
        """
        self.start_time = time

    def start(self, *args, **kwargs):
        """
            Start the EventLoop, creating a task and adding it to the loop
        :param args: Arguments to run the loop with
        :param kwargs: Keyword arguments to run the loop with
        """
        log.info(f"Starting event loop {self.name}")
        if self.parent is not None:
            newargs = [self.parent]
            newargs.extend(args)
            args = tuple(newargs)
        self._task = self.loop.create_task(self.run(*args, **kwargs))

    async def run(self, *args, **kwargs):
        """
            Actual runner of the EventLoop. Aligns the periods, and does error handling. Should propagate no Exceptions,
            though warnings or errors will be logged on persist or killing error.
        :param args: Arguments to run the loop with
        :param kwargs: Keyword arguments to run the loop with
        """
        if self.start_time is not None:
            now = dt.datetime.utcnow()
            delta = self.start_time - now
            await asyncio.sleep(delta.total_seconds())
        else:
            delta = align_period(self.period)
            await asyncio.sleep(delta.total_seconds())
        while True:
            try:
                log.debug(f"Running event loop {self.name}")
                await self._callback(*args, **kwargs)
            except errors.StopEventLoop as e:
                if e.message:
                    log.warning(e.message)
                return
            except Exception as e:
                if self.persist:
                    utils.log_error(log, logging.WARNING, e, f"Ignoring error in event loop {self.name}:")
                else:
                    utils.log_error(log, logging.ERROR, e, f"Stopping event loop {self.name}:")
                    self._task = None
                    return
            delta = align_period(self.period)
            await asyncio.sleep(delta.total_seconds())

    def stop(self):
        """
            Stop the EventLoop. Cancels the task, does any cleanup
        """
        if self._task is not None:
            log.info(f"Stopping event loop {self.name}")
            self._task.cancel()
            self._task = None


def eventloop(period, **kwargs):
    """
        Decorator to turn a coroutine into an EventLoop
    :param period: Length of time between loop repititions, generally a string like 1m3s
    :param kwargs: Arguments to pass to the EventLoop constructor
    :return: Internal callback
    """

    def decorator(coro):
        return EventLoop(coro, period, **kwargs)

    return decorator
