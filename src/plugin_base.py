from enum import Enum


class PluginType(Enum):
    SONG_INFO_PLUGIN = 0
    MESSAGING_PLUGIN = 1

class PluginBase:
    """! Base class of plugins

        Plugins are extensions of the base program to enable advanced features
    """
    player_window = None      # Reference to the display window
    maintenance_frame = None  # Reference to the maintenance frame in the sequencer window, to add UI controls

    def __init__(self):
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
        """! Returns True if the plugin needs a maintenance frame, for UI controls """
        # The base class doesnt need a maintenance frame
        return False

    def get_name(self):
        return "unknown"