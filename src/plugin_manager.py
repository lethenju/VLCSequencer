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

from plugins.song_info_plugin import SongInfoPlugin
from plugins.messaging_plugin import MessagingPlugin
from plugin_base import *

class PluginManager:
    """! Functionnal overlays of the """
    active_plugins = []

    def __init__(self):
        """! Creates the plugin manager """
        self.active_plugins = []
    
    def get_plugins(self):
        return self.active_plugins
    
    def add_plugin(self, type_of_plugin, params = None):
        """! Add a plugin with some params as a dictionnary 
            @param type_of_plugin : enum of the plugin type, as defined in the PluginType definition
            @param params : reference to the parameters of the plugins
        """
        if type_of_plugin == PluginType.SONG_INFO_PLUGIN:
            # For now, no params in the song info plugin
            self.active_plugins.append(SongInfoPlugin())
        elif type_of_plugin == PluginType.MESSAGING_PLUGIN:
            self.active_plugins.append(MessagingPlugin(params))   
            