# Copyright (C) 2023 Julien LE THENO
#
# This file is part of the VLCSequencer package
# See github.com/lethenju/VLCSequencer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import tkinter as tk
from time import sleep, time
from threading import Thread

from colors import *
from logger import PrintTraceInUi
from plugin_base import PluginBase

class TimeAndChannelPlugin(PluginBase):
    """! Plugin to show the song info as it plays """
    frame_time_channel = None

# Plugin interface
    def setup(self, **kwargs):
        """! Setup """

        if super().player_window is None and "player_window" in kwargs:
            super().setup(player_window=kwargs["player_window"])

    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """
        if self.frame_time_channel is not None:
            # TODO Update time
            pass

    def on_exit(self):
        """! Called at the end of a video playback """

    def is_maintenance_frame(self):
        """! Returns if the plugins has a maintenance frame """
        # No maintenance frame for this plugin, as for now
        return False

    def get_name(self):
        return "Time and Channel"

    def on_destroy(self):
        super().on_destroy()

