
import http.server
import socketserver
import time
import threading
import tkinter as tk

from colors import *

HTTP_PORT = 8000


class MessagingPlugin:
    """! Plugin to show live messages under the video """
    tk_window = None

    http_server = None
    server_thread = None

    def __init__(self, tk_window):
        """! Links to the Tkinter Window """
        self.tk_window = tk_window
        # Create an object of the above class
        self.http_server = socketserver.TCPServer(("", HTTP_PORT), self.MyHttpRequestHandler)
        self.server_thread = threading.Thread(target=self.http_server.serve_forever)
        self.server_thread.start()

        # TODO Start messaging broadcasting thread

# Plugin interface

    def setup(self, **kwargs):
        """! Setup """
        # Rien de particulier

    def on_begin(self):
        """! Called at the beginning of a video playback """
        # TODO bIsShowAsked = True

    def on_progress(self, time_s):
        """! Called every second of a video playback """

    def on_exit(self):
        """! Called at the end of a video playback """
        # TODO bIsExitAsked = False

# Private members

    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.path = 'src/static/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
    class MessagingUiThread:

        def __init__(self):
            """! Init """
            # TODO Implement
        
        def runtime(self):
            """! Runtime """
            # TODO Implement
        
        def show(self):
            """! Show api """
            #

        def hide(self):
            """! hide api """

