from enum import Enum


class PluginType(Enum):
    SONG_INFO_PLUGIN = 0
    MESSAGING_PLUGIN = 1

class PluginBase:
    tk_window = None

    def __init__(self):
        """! Links to the Tkinter Window """
        self.is_running = True

    # Plugin interface
    def setup(self, **kwargs):
        """! Setup the plugins with custom parameters """
        if "tk_window" in kwargs:
            self.tk_window = kwargs["tk_window"]
        

    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """

    def on_exit(self):
        """! Called at the end of a video playback """
    
    def on_destroy(self):
        """! Called to stop the plugin and release resources """
        self.is_running = False
