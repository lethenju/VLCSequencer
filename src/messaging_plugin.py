
import tkinter as tk

from colors import *

class MessagingPlugin:
    """! Plugin to show live messages under the video """
    tk_window = None

    def __init__(self, tk_window):
        """! Links to the Tkinter Window """
        self.tk_window = tk_window

# Plugin interface

    def setup(self):
        """! Setup """

    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """

    def on_exit(self):
        """! Called at the end of a video playback """
        


# Private functions
