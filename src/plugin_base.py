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

from enum import Enum


class PluginType(Enum):
    SONG_INFO_PLUGIN = 0
    MESSAGING_PLUGIN = 1
    TIME_AND_CHANNEL_PLUGIN = 2

    def plugin_type_factory(str_name):
        """! Returns the appropriate enum with the name of the plugin """
        if str_name == "SongInfo":
            return PluginType.SONG_INFO_PLUGIN
        if str_name == "Messaging":
            return PluginType.MESSAGING_PLUGIN
        if str_name == "TimeAndChannel":
            return PluginType.TIME_AND_CHANNEL_PLUGIN

        # A plugin name should always be defined
        # FIXME
        assert False


class PluginBase:
    """! Base class of plugins

        Plugins are extensions of the base program to enable advanced features
    """
    # Reference to the display window
    player_window = None
    # Reference to the maintenance frame in the sequencer window,
    # to add UI controls
    maintenance_frame = None

    def __init__(self, params=None):
        self.params = params
        self.is_running = True

    # Plugin interface
    def setup(self, **kwargs):
        """! Setup the plugins with custom parameters """
        if "player_window" in kwargs:
            self.player_window = kwargs["player_window"]
        if "maintenance_frame" in kwargs:
            self.maintenance_frame = kwargs["maintenance_frame"]

    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """

    def on_exit(self):
        """! Called at the end of a video playback """

    def on_destroy(self):
        """! Called to stop the plugin and release resources """
        self.is_running = False

    def is_maintenance_frame(self):
        """! Returns True if the plugin needs a maintenance frame,
            for UI controls """
        # The base class doesnt need a maintenance frame
        return False

    def get_name(self):
        """! Returns the name of the plugin """
        # The derived class didnt implement
        # this function
        return "unknown"
