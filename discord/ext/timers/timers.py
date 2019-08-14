# -*- coding: utf-8 -*-

import collections.abc
import datetime

from .utils import ListBasedQueue, chunked_sleep


class ChildTimer:
    """A slimmed down timer class meant for internal use."""

    def __init__(self, name, expires, args=None, kwargs=None):
        if not isinstance(args, collections.abc.Iterable) and args is not None:
            raise TypeError("args must be an iterable, got {0!r}".format(args.__class__.__name__))

        if kwargs is not None and not isinstance(kwargs, dict):
            raise TypeError("kwargs must be of type dict, got {0!r}".format(args.__class__.__name__))

        if kwargs is not None:
            if not all(isinstance(key, str) for key in kwargs.keys()):
                raise TypeError("kwargs keys must all be str")

        self._expires = self._convert_to_expires(expires)

        self.name = name
        self._args = args or tuple()
        self._kwargs = kwargs or {}

    def _convert_to_expires(self, expires):
        if isinstance(expires, (float, int)):
            return datetime.datetime.utcnow() + datetime.timedelta(seconds=expires)
        elif isinstance(expires, datetime.timedelta):
            return datetime.datetime.utcnow() + expires
        elif isinstance(expires, datetime.datetime):
            return expires
        else:
            raise TypeError(
                "expires must be one of int, float, datetime.datetime or datetime.timedelta. Got {0!r}".format(
                    expires.__class__.__name__
                )
            )


class Timer(ChildTimer):
    """A timer that spawns his own task.

    Parameters
    ----------
    bot: :class:`discord.Client`
        A discord.py client instance.
    name: :class:`str`
        Same as in :meth:`TimerManager.create_timer`.
    expires: Union[:class:`float`, :class:`int`, :class:`datetime.datetime`, :class:`datetime.timedelta`]
        Same as in :meth:`TimerManager.create_timer`.
    args: :class:`~collections.abc.Iterable`
        Same as in :meth:`TimerManager.create_timer`.
    kwargs: Mapping[:class:`str`, Any]
        Same as in :meth:`TimerManager.create_timer`.
    """

    def __init__(self, bot, name, expires, args=None, kwargs=None):
        super().__init__(name, expires, args, kwargs)

        self._bot = bot
        self._task = None

    async def internal_task(self):
        await chunked_sleep((self._expires - datetime.datetime.utcnow()).total_seconds())

        self._bot.dispatch(self.name, *self._args, **self._kwargs)

    @property
    def done(self):
        """::class:`bool` Whether the timer is done."""
        return self._task is not None and self._task.done()

    def start(self):
        """Start the timer.

        Returns
        -------
        :class:`Timer`
            The Timer started."""
        self._task = self._bot.loop.create_task(self.internal_task())

        return self

    def _check_task(self):
        if self._task is None:
            raise RuntimeError("Timer was never started.")
        if self._task.done():
            raise RuntimeError("Timer is already done.")

    def cancel(self):
        """Cancel the timer.

        Raises
        ------
        RuntimeError
            The timer was not launched or is already done."""
        self._check_task()

        self._task.cancel()

    @property
    def remaining(self):
        """::class:`int` The amount of seconds before the timer is done."""
        return (self._expires - datetime.datetime.utcnow()).total_seconds()

    async def join(self):
        """Wait until the timer is done.

        Raises
        ------
        RuntimeError
            The timer was not launched or is already done."""
        self._check_task()

        await self._task


class TimerManager:
    """A class that manages timer dispatching with a single task.

    Parameters
    ----------
    bot: :class:`discord.Client`
        A discord.py client instance."""

    def __init__(self, bot):
        self._bot = bot
        self.__timers = ListBasedQueue(loop=bot.loop)
        self._current_timer = None

        self._task = self._bot.loop.create_task(self.poll_timers())

    async def poll_timers(self):
        while True:
            self._current_timer = timer = await self.__timers.get()
            self.__timers.task_done()

            time = (timer._expires - datetime.datetime.utcnow()).total_seconds()

            await chunked_sleep(time)

            self._bot.dispatch(timer.name, *timer._args, **timer._kwargs)

    def create_timer(self, name, expires, args=None, kwargs=None):
        """Create a timer to be scheduled for dispatching

        Arguments
        ---------
        name: :class:`str`
            The name under which an event will be dispatched when the timer is complete.
        expires: Union[:class:`float`, :class:`int`, :class:`datetime.datetime`, :class:`datetime.timedelta`]
            If a :class:`float` or :class:`int`, the amount of seconds to sleep.
            If a :class:`datetime.datetime`, the UTC date at which the timer will finish.
            If a :class:`datetime.timedelta`, the delta relative to the current UTC date at which the timer will finish.
        args: :class:`~collections.abc.Iterable`
            An iterable of positional arguments passed to the dispatched event.
        kwargs: Mapping[:class:`str`, Any]
            A mapping of keyword arguments passed to the dispatched event.
        """

        # ok so this is literally the biggest cluster fuck I have ever created ever
        # please bear with me for a second ok? ok
        # if you have any ideas on how to make this better I'll be glad to hear them

        # we create a child timer, which is basically just a fancy dataclass
        timer = ChildTimer(name, expires, args, kwargs)

        # if there's a currently running timer and it will take more time then the new one
        if self._current_timer is not None and self._current_timer._expires > timer._expires:
            # cancel the task
            self._task.cancel()

            # put back in the current timer + the new one
            self.__timers.put_nowait(self._current_timer)
            self.__timers.put_nowait(timer)
            # sort it so the new one will be the first one
            self.__timers._queue.sort(key=lambda x: x._expires)

            # restart the polling
            self._task = self._bot.loop.create_task(self.poll_timers())
        else:
            # else let's just put the new timer in the queue
            self.__timers.put_nowait(timer)
            # and keep it sorted
            self.__timers._queue.sort(key=lambda x: x._expires)

    @property
    def done(self):
        """::class:`bool` Whether or not the enternal task is done."""
        return self._task.done()

    def cancel(self):
        """Cancel the internal task.

        Raises
        ------
        RuntimeError
            The manager is already done.
        """
        if self._task.done():
            raise RuntimeError("The manager is already done.")
        self._task.cancel()

    def clear(self):
        """Clear the timer queue and restart the internal task."""
        if not self._task.done():
            self._task.cancel()
        self.__timers = ListBasedQueue(loop=self._bot.loop)

        self._task = self._bot.loop.create_task(self.poll_timers())

    async def join(self):
        """Wait until there are no more timers to dispatch."""
        await self.__timers.join()
