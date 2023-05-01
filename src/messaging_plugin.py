
import http.server
import socketserver
import threading
import tkinter as tk
from urllib import parse

from colors import *
from logger import PrintTraceInUi

HTTP_PORT = 8000


class MessagingPlugin:
    """! Plugin to show live messages under the video """
    tk_window = None
    is_running = False

    http_server = None
    server_thread = None

    def __init__(self, tk_window):
        """! Links to the Tkinter Window """
        self.tk_window = tk_window
        self.is_running = True
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

    def on_destroy(self):
        """! Called to stop the plugin and release resources """
        self.is_running = False
        self.http_server.shutdown()
        self.server_thread.join()

# Private members

    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

        def do_GET(self):
            #Only one page
            self.path = 'src/static/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        def do_POST(self):
            PrintTraceInUi("Received a message !")
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            fields = parse.parse_qs(str(data_string,"UTF-8"))
            PrintTraceInUi(fields)

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

