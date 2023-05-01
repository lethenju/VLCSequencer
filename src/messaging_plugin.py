
import http.server
import socketserver
import threading
import tkinter as tk
from time import time, sleep
from urllib import parse
from functools import partial

from colors import *
from logger import PrintTraceInUi

HTTP_PORT = 8000

class MessagingPlugin:
    """! Plugin to show live messages under the video """
    tk_window = None
    is_running = False

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

    def __init__(self, tk_window):
        """! Links to the Tkinter Window """
        self.tk_window = tk_window
        self.is_running = True

        # TODO Maybe store/read active messages in file 
        self.message_ui = self.MessagingUiThread(tk_window)
        self.message_ui_thread = threading.Thread(target=self.message_ui.runtime).start()

        self.http_server = socketserver.TCPServer(("", HTTP_PORT), partial(self.MyHttpRequestHandler, self.message_ui.add_message))
        self.server_thread = threading.Thread(target=self.http_server.serve_forever)
        self.server_thread.start()

# Plugin interface

    def setup(self, **kwargs):
        """! Setup """
        # Rien de particulier

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
            if self.cb_add_message is not None:
                self.cb_add_message(MessagingPlugin.Message(fields["name"][0], fields["message"][0]))
            self.send_response(200)
        

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
            self.frame_messages = tk.Frame(self.tk_window, width=100, bg=UI_BACKGROUND_COLOR)

            font_size = int(self.tk_window.winfo_height() /25);
            PrintTraceInUi("FontSize ", font_size)
            self.active_label_author  = tk.Label(self.frame_messages,text="", padx=10, pady=10, font=('calibri', font_size, 'bold'),fg="white", bg=UI_BACKGROUND_COLOR)
            self.active_label_message = tk.Label(self.frame_messages,text="", padx=10, pady=10, font=('calibri', font_size),fg="white", bg=UI_BACKGROUND_COLOR)
            
            self.active_label_author .pack(side=tk.LEFT)
            self.active_label_message.pack(side=tk.RIGHT)
        
        def runtime(self):
            """! Runtime """
            PrintTraceInUi("Messaging UI Runtime")
            while self.is_running:
                if len(self.active_messages) > 0:
                    self.index_sequence_message = (self.index_sequence_message + 1) % len(self.active_messages)
                    PrintTraceInUi("Index of current message = ", self.index_sequence_message, " Author : ",  
                        self.active_messages[self.index_sequence_message].author, " Message ",
                        self.active_messages[self.index_sequence_message].message)
                    self.active_label_author.configure(text = self.active_messages[self.index_sequence_message].author)
                    self.active_label_message.configure(text = self.active_messages[self.index_sequence_message].message)
                sleep(5)

            self.frame_messages.destroy()

        def add_message(self, message):
            """! Adding a message in the dictionary of active message """
            self.active_messages.append(message)

        def show(self):
            """! Show api """
            PrintTraceInUi("Show message UI")
            self.is_shown = True
            self.frame_messages.place(x=0, y= 0.9 * self.tk_window.winfo_height() )

        def hide(self):
            """! hide api """
            PrintTraceInUi("Hide message UI")
            self.is_shown = False
            self.frame_messages.place(x=0, y= 1.1 * self.tk_window.winfo_height() )

        def stop(self):
            self.is_running = False