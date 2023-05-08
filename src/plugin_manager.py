from song_info_plugin import SongInfoPlugin
from messaging_plugin import MessagingPlugin
from plugin_base import *

class PluginManager:
    active_plugins = []

    def __init__(self):
        """! Creates the plugin manager """
        self.active_plugins = []
    
    def get_plugins(self):
        return self.active_plugins
    
    def add_plugin(self, type_of_plugin):
        #self.active_plugins.append(PluginType[type_of_plugin])
        if type_of_plugin == PluginType.SONG_INFO_PLUGIN:
            self.active_plugins.append(SongInfoPlugin())
        elif type_of_plugin == PluginType.MESSAGING_PLUGIN:
            self.active_plugins.append(MessagingPlugin())   
            