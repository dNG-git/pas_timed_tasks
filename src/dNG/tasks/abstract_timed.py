# -*- coding: utf-8 -*-

"""
direct PAS
Python Application Services
----------------------------------------------------------------------------
(C) direct Netware Group - All rights reserved
https://www.direct-netware.de/redirect?pas;timed_tasks

The following license agreement remains valid unless any additions or
changes are being made by direct Netware Group in a written form.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
----------------------------------------------------------------------------
https://www.direct-netware.de/redirect?licenses;gpl
----------------------------------------------------------------------------
#echo(pasTimedTasksVersion)#
#echo(__FILEPATH__)#
"""

# pylint: disable=import-error, no-name-in-module

from threading import Timer
from time import time

from dNG.plugins.hook import Hook
from dNG.runtime.not_implemented_exception import NotImplementedException
from dNG.runtime.thread import Thread
from dNG.runtime.thread_lock import ThreadLock

class AbstractTimed(object):
    """
Timed tasks provides an abstract, time ascending sorting scheduler.

:author:     direct Netware Group et al.
:copyright:  (C) direct Netware Group - All rights reserved
:package:    pas
:subpackage: timed_tasks
:since:      v1.0.0
:license:    https://www.direct-netware.de/redirect?licenses;gpl
             GNU General Public License 2
    """

    # pylint: disable=unused-argument

    def __init__(self):
        """
Constructor __init__(AbstractTimed)

:since: v1.0.0
        """

        self.lock = ThreadLock()
        """
Thread safety lock
        """
        self._log_handler = None
        """
The LogHandler is called whenever debug messages should be logged or errors
happened.
        """
        self.timer = None
        """
"Timer" instance
        """
        self.timer_active = False
        """
UNIX timestamp of the next element
        """
        self.timer_timestamp = -1
        """
UNIX timestamp of the next element
        """
    #

    def __del__(self):
        """
Destructor __del__(AbstractTimed)

:since: v1.0.0
        """

        self.stop()
    #

    @property
    def is_started(self):
        """
Returns true if the timed tasks implementation has been started.

:return: (bool) True if scheduling is active
:since:  v1.0.0
        """

        return self.timer_active
    #

    @property
    def _next_update_timestamp(self):
        """
Get the implementation specific next "run()" UNIX timestamp.

:return: (float) UNIX timestamp; -1 if no further "run()" is required at the
         moment
:since:  v1.0.0
        """

        raise NotImplementedException()
    #

    def run(self):
        """
Timed task execution

:since: v1.0.0
        """

        if (self.timer_active):
            with self.lock:
                # Thread safety
                self.timer_timestamp = -1
                if (self.timer_active): self.update_timestamp()
            #
        #
    #

    def start(self, params = None, last_return = None):
        """
Start the timed tasks implementation.

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:since: v1.0.0
        """

        if (not self.timer_active):
            with self.lock:
                # Thread safety
                if (not self.timer_active):
                    Hook.register_weakref("dNG.pas.Status.onShutdown", self.stop)

                    self.timer_active = True
                    self.timer_timestamp = -1
                    self.update_timestamp()
                #
            #
        #
    #

    def stop(self, params = None, last_return = None):
        """
Stop the timed tasks implementation.

:param params: Parameter specified
:param last_return: The return value from the last hook called.

:since: v1.0.0
        """

        with self.lock:
            if (self.timer_active):
                if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -{0!r}.stop()- (#echo(__LINE__)#)", self, context = "pas_timed_tasks")

                self.timer_active = False
                Hook.unregister("dNG.pas.Status.onShutdown", self.stop)
            #

            if (self.timer is not None and self.timer.is_alive()): self.timer.cancel()
            self.timer = None
        #
    #

    def update_timestamp(self, timestamp = -1):
        """
Update the timestamp for the next "run()" call.

:param timestamp: Externally defined UNIX timestamp of the next scheduled
                  run.

:since: v1.0.0
        """

        if (self._log_handler is not None): self._log_handler.debug("#echo(__FILEPATH__)# -{0!r}.update_timestamp({1})- (#echo(__LINE__)#)", self, timestamp, context = "pas_timed_tasks")

        if (self.timer_active):
            thread = None

            with self.lock:
                # Thread safety
                timeout = -1

                if (self.timer_active):
                    if (timestamp < 0): timestamp = self._next_update_timestamp

                    if (timestamp > 0):
                        timeout = timestamp - time()
                        if (timeout < 0): timeout = 0
                    #
                #

                if (timeout < 0):
                    if (self.timer is not None and self.timer.is_alive()):
                        self.timer.cancel()
                        self.timer_timestamp = -1
                    #
                elif (self.timer_timestamp < 0 or timestamp < self.timer_timestamp):
                    if (self.timer is not None and self.timer.is_alive()): self.timer.cancel()

                    if (timeout > 0):
                        self.timer = Timer(timeout, self.run)
                        self.timer_timestamp = timestamp

                        if (self._log_handler is not None): self._log_handler.debug("{0!r} waits for {1} seconds", self, timeout, context = "pas_timed_tasks")
                        self.timer.start()
                    else:
                        if (self._log_handler is not None): self._log_handler.debug("{0!r} continues with the next step", self, context = "pas_timed_tasks")

                        thread = Thread(target = self.run)
                    #
                #
            #

            if (thread is not None): thread.start()
        #
    #
#
