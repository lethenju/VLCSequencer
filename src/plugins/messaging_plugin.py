
import http.server
import socketserver
import threading
import tkinter as tk
from time import time, sleep
from urllib import parse
from functools import partial

from colors import *
from logger import PrintTraceInUi
from plugin_base import PluginBase

HTTP_PORT = 8000

class MessagingPlugin(PluginBase):
    """! Plugin to show live messages under the video """
    http_server = None
    server_thread = None

    message_ui = None
    message_ui_thread = None

    class Message:
        author = ""
        message = ""
        timestamp_activation = None
        def __init__(self, author, message):
            """! Initialization of a message """

            self.author = author
            self.message = message
            self.timestamp_activation = time()

# Plugin interface

    def setup(self, **kwargs):
        """! Setup """

        if self.tk_window is None and "tk_window" in kwargs:
            PrintTraceInUi("Setup of the messaging plugin")
            super().setup(tk_window=kwargs["tk_window"])
            # TODO Maybe store/read active messages in file 
            self.message_ui = self.MessagingUiThread(self.tk_window)
            self.message_ui_thread = threading.Thread(target=self.message_ui.runtime).start()

            self.http_server = socketserver.TCPServer(("", HTTP_PORT), partial(self.MyHttpRequestHandler, self.message_ui.add_message))
            self.server_thread = threading.Thread(target=self.http_server.serve_forever)
            self.server_thread.start()


    def on_begin(self):
        """! Called at the beginning of a video playback """
        self.message_ui.show()

    def on_progress(self, time_s):
        """! Called every second of a video playback """
        
    def on_exit(self):
        """! Called at the end of a video playback """
        #  For now, message bar stays on
        # self.message_ui.hide()

    def on_destroy(self):
        """! Called to stop the plugin and release resources """
        self.is_running = False
        self.message_ui.stop()
        self.http_server.shutdown()
        self.server_thread.join()

# Private members

    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
        
        cb_add_message = None
        def __init__(self, cb_add_message, *args, **kwargs):
            self.cb_add_message = cb_add_message
            super().__init__(*args, **kwargs)

        def do_GET(self):
            #Only one page
            self.path = 'src/static/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        def do_POST(self):
            PrintTraceInUi("Received a message !")
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            fields = parse.parse_qs(str(data_string,"UTF-8"))
            PrintTraceInUi(fields)
            # Subscribe the message in the active list 
            if self.cb_add_message is not None and "message" in fields and "name" in fields:
                message = fields["message"][0].replace('\n', '')
                # Check if the message is not too long
                self.cb_add_message(MessagingPlugin.Message(fields["name"][0], message))
            self.path = 'src/static/done.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        

    class MessagingUiThread:
        active_messages = []
        is_shown = False
        tk_window = None

        frame_messages = None
        active_label_author = ""
        active_label_message = ""
        index_sequence_message = 0

        is_running = False

        def __init__(self, tk_root):
            """! Init """
            self.tk_window = tk_root
            self.is_shown = False 
            self.is_running = True
            self.frame_messages = tk.Frame(self.tk_window, bg=UI_BACKGROUND_COLOR)

            font_size = int(self.tk_window.winfo_height() /20);
            PrintTraceInUi("FontSize ", font_size)
            self.active_label_author  = tk.Label(self.frame_messages,text="", padx=10, pady=1, font=('calibri', font_size, 'bold'),fg="white", bg=UI_BACKGROUND_COLOR)
            self.active_label_message = tk.Label(self.frame_messages,text="", padx=10, pady=1, font=('calibri', font_size),fg="white", bg=UI_BACKGROUND_COLOR)
            
            self.active_label_author .pack(side=tk.LEFT, anchor=tk.CENTER)
            self.active_label_message.pack(side=tk.LEFT, anchor=tk.CENTER)
        
        def runtime(self):
            """! Runtime """
            PrintTraceInUi("Messaging UI Runtime")
            while self.is_running:
                self._compute_messages()
                if len(self.active_messages) > 0:
                    self.index_sequence_message = (self.index_sequence_message + 1) % len(self.active_messages)
                    PrintTraceInUi("Index of current message = ", self.index_sequence_message, " Author : ",  
                        self.active_messages[self.index_sequence_message].author, " Message ",
                        self.active_messages[self.index_sequence_message].message)
                        
                    font_size = int(self.tk_window.winfo_height() /20);
                    PrintTraceInUi("FontSize ", font_size)
                    self.active_label_author.configure(text = self.active_messages[self.index_sequence_message].author, 
                        font=('calibri', font_size, 'bold'))
                    self.active_label_message.configure(text = self.active_messages[self.index_sequence_message].message,
                        font=('calibri', font_size))
                sleep(5)

            self.frame_messages.destroy()

        def add_message(self, message):
            """! Adding a message in the dictionary of active message """
            
            # Remove messages with the same author 
            self.active_messages = list(filter(lambda active_message: (
                active_message.author != message.author), self.active_messages))

            self.active_messages.append(message)
            #Recompute show (we now have messages)
            if self.is_shown:
                self.show()

        def show(self):
            """! Show api """
            PrintTraceInUi("Show message UI")
            self.is_shown = True
            if len(self.active_messages) > 0:
                self.frame_messages.place(relx=0, rely= 0.95, relheight=0.05, relwidth=1)

        def hide(self):
            """! hide api """
            PrintTraceInUi("Hide message UI")
            self.is_shown = False
            self.frame_messages.place(relx=0, rely= 0.95, relheight=0, relwidth=1)

        def stop(self):
            self.is_running = False
        
        def _compute_messages(self):
            # If its been more than 10 minutes, the message disappears from the sequence
            PrintTraceInUi("Recomputing messages..")
            self.active_messages = list(filter(lambda message: (
                message.timestamp_activation + 10*60 > time()), self.active_messages))
