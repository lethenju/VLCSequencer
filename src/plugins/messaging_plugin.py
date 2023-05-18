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

import http.server
import socketserver
import threading
import tkinter as tk
from time import time, sleep
from datetime import datetime
from urllib import parse
from functools import partial
from dataclasses import dataclass

from colors import *
from logger import PrintTraceInUi
from plugin_base import PluginBase
from plugins.messaging_view import MessageListbox

PORT_PARAM = "Port"
PORT_PARAM_DEFAULT = "8000"
DISPLAY_TIME_PARAM = "DisplayTime"
DISPLAY_TIME_PARAM_DEFAULT = "5"
DISPLAY_TIME_LONG_MESSAGE_PARAM = "DisplayTimeLongMessage"
DISPLAY_TIME_LONG_MESSAGE_PARAM_DEFAULT = "15"
DELETE_AFTER_MINUTES_PARAM = "DeleteAfterMinutes"
DELETE_AFTER_MINUTES_PARAM_DEFAULT = "10"

MESSAGE_FILE_PATH_PARAM = "MessageFilePath"


class MessagingPlugin(PluginBase):
    """! Plugin to show live messages under the video """
    http_server = None
    server_thread = None

    message_ui = None
    message_ui_thread = None

    maintenance_listbox = None
    is_server_running = False
    
    def __init__(self, params = None):
        super().__init__(params)
        
        if PORT_PARAM not in self.params:
            PrintTraceInUi(f"{PORT_PARAM} is not defined, use default value")
            self.params[PORT_PARAM] = PORT_PARAM_DEFAULT
        if DISPLAY_TIME_PARAM not in self.params:
            PrintTraceInUi(f"{DISPLAY_TIME_PARAM} is not defined, use default value")
            self.params[DISPLAY_TIME_PARAM] = DISPLAY_TIME_PARAM_DEFAULT
        if DISPLAY_TIME_LONG_MESSAGE_PARAM not in self.params:
            PrintTraceInUi(f"{DISPLAY_TIME_LONG_MESSAGE_PARAM} is not defined, use default value")
            self.params[DISPLAY_TIME_LONG_MESSAGE_PARAM] = DISPLAY_TIME_LONG_MESSAGE_PARAM_DEFAULT
        if DELETE_AFTER_MINUTES_PARAM not in self.params:
            PrintTraceInUi(f"{DELETE_AFTER_MINUTES_PARAM} is not defined, use default value")
            self.params[DELETE_AFTER_MINUTES_PARAM] = DELETE_AFTER_MINUTES_PARAM_DEFAULT

    @dataclass
    class Message:
        author : str
        message : str
        timestamp_activation : float

        _is_active : bool = False
        _is_current_message_shown : bool = False

        _active_state_cb : any = None
        _current_message_state_cb : any = None

        def set_current_message(self):
            if not self._is_active:
                PrintTraceInUi(f"This message is not active ! {self.message}")
            PrintTraceInUi(f"Message is shown")
            self._is_current_message_shown = True
            if self._current_message_state_cb is not None:
                self._current_message_state_cb(True)

        def set_not_current_message(self):
            if not self._is_active:
                PrintTraceInUi(f"This message is not active ! {self.message}")
            self._is_current_message_shown = False
            if self._current_message_state_cb is not None:
                self._current_message_state_cb(False)
        
        def set_active(self):
            self._is_active = True
            if self._active_state_cb is not None:
                self._active_state_cb(True)
        
        def set_inactive(self):
            self._is_active = False
            if self._active_state_cb is not None:
                self._active_state_cb(False)

        def is_current_message(self):
            return self._is_current_message_shown
        
        def is_active(self):
            return self._is_active
        
        def store_active_state_cb(self, active_state_cb):
            self._active_state_cb = active_state_cb
        
        def store_current_message_cb(self, current_message_state_cb):
            self._current_message_state_cb = current_message_state_cb
        

# Plugin interface


    def start_server(self):
        if not self.is_server_running:
            PrintTraceInUi("Starting http server")
            self.server_thread = threading.Thread(name="HTTP Server Thread", target=self.my_serve_forever)
            self.is_server_running = True
            self.server_thread.start()
        else:
            PrintTraceInUi("Server is already started")
    
    def stop_server(self):
        if self.is_server_running:
            PrintTraceInUi("Stopping http server")
            self.is_server_running = False    
            self.server_thread.join(timeout=2)
            if self.server_thread.is_alive():
                PrintTraceInUi("ERR : Thread is still active !")
            else:
                PrintTraceInUi("Thread is correctly stopped")
                self.server_thread = None
        else:
            PrintTraceInUi("Server is already stopped")

    def my_serve_forever(self):
        """! Little helper serve_forever thread function for the http server
                that stops if the is_server_running method is stopped
        """
        PrintTraceInUi("HTTP Server Thread begin")
        # Set an 1 second timeout for server handling request
        self.http_server.timeout = 1
        while self.is_server_running:
            PrintTraceInUi("HTTP Server Thread Handling request")
            self.http_server.handle_request()
        

    def setup(self, **kwargs):
        """! Setup """

        if self.player_window is None and "player_window" in kwargs:
            PrintTraceInUi("Link player window to us")
            super().setup(player_window=kwargs["player_window"])

            # TODO Maybe store/read active messages in file 
            self.message_ui = self.MessagingUiThread(self.player_window, self.params)
            self.message_ui_thread = threading.Thread(name="MessageUI Thread", target=self.message_ui.runtime)
            self.message_ui_thread.start()

            self.http_server = socketserver.TCPServer(("", int(self.params[PORT_PARAM])), partial(self.MyHttpRequestHandler, self.message_ui.add_message))

        if self.maintenance_frame is None and "maintenance_frame" in kwargs:
            PrintTraceInUi("Link maintenance window to us")
            super().setup(maintenance_frame=kwargs["maintenance_frame"])
            PrintTraceInUi("Setup")

            # status maintenance view 
            # Provide info about the server/UI being active and provide options
            # to enable and disable the server/UI

            self.status_frame = tk.Frame(self.maintenance_frame, bg=UI_BACKGROUND_COLOR)
            self.status_frame.pack(side=tk.TOP, fill=tk.X)

            self.server_status_frame = tk.Frame(self.status_frame, bg=UI_BACKGROUND_COLOR)
            self.server_status_frame.pack(side=tk.LEFT, fill=tk.BOTH)
            
            self.message_ui_status_frame = tk.Frame(self.status_frame, bg=UI_BACKGROUND_COLOR)
            self.message_ui_status_frame.pack(side=tk.RIGHT, fill=tk.BOTH)


            self.server_status_label = tk.Label(self.server_status_frame, text="Server is currently inactive", font=('calibri', 11, 'bold'),fg="white", bg=UI_BACKGROUND_COLOR)
            self.server_status_label.pack(side=tk.LEFT)

            self.message_ui_status_label = tk.Label(self.message_ui_status_frame, text="Message UI is currently active", font=('calibri', 11, 'bold'),fg="white", bg=UI_BACKGROUND_COLOR)
            self.message_ui_status_label.pack(side=tk.LEFT)


            def server_toggle_button_cmd():
                if self.is_server_running:
                    self.stop_server()
                    self.server_status_label.configure(text="Server is currently inactive")
                else:
                    self.start_server() 
                    self.server_status_label.configure(text="Server is currently active")

            def show_toggle_button_cmd():
                if self.message_ui.is_shown:
                    self.message_ui.hide()
                    self.message_ui_status_label.configure(text="Message UI is inactive")
                else:
                    self.message_ui.show()
                    self.message_ui_status_label.configure(text="Message UI is active")

            
            self.server_toggle_button = tk.Button(self.server_status_frame, text="Toggle server state", font=('calibri', 11),fg="white",
             bg=UI_BACKGROUND_COLOR, command=server_toggle_button_cmd)
            self.server_toggle_button.pack(side=tk.RIGHT)

            self.message_ui_toggle_button = tk.Button(self.message_ui_status_frame, text="Toggle UI state", font=('calibri', 11),fg="white",
             bg=UI_BACKGROUND_COLOR, command=show_toggle_button_cmd)
            self.message_ui_toggle_button.pack(side=tk.RIGHT)

            self.list_frame = tk.Frame(self.maintenance_frame)

            # Create listbox
            self.maintenance_listbox = MessageListbox(self.list_frame)
            self.list_frame.pack(side=tk.BOTTOM,fill=tk.BOTH, expand=True)

        
        if self.maintenance_listbox is not None and self.message_ui is not None:
            # Everything is loaded
            self.message_ui.subscribe_listbox(self.maintenance_listbox)

            # TODO Load file messages


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
        self.stop_server()
        self.message_ui_thread.join()
        # FIXME Workaround to stop the tcp server 
        self.http_server._BaseServer__shutdown_request = True
        # self.http_server = None

    def is_maintenance_frame(self):
        """! Returns True if the plugin needs a maintenance frame, for UI controls """
        # We need a maintenance frame in the messaging plugin :
        # Listbox display current and old messages
        return True
    
    def get_name(self):
        return "Messaging"
# Private members

    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
        
        cb_add_message = None
        def __init__(self, cb_add_message, *args, **kwargs):
            self.cb_add_message = cb_add_message
            super().__init__(*args, **kwargs)

        def do_GET(self):
            if self.path == "/style.css":
                self.path = "src/static/style.css"
            else:
                self.path = "src/static/index.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        def do_POST(self):
            PrintTraceInUi("Received a message !")
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            fields = parse.parse_qs(str(data_string,"UTF-8"))
            PrintTraceInUi(fields)
            # Subscribe the message in the active list 
            if self.cb_add_message is not None and "message" in fields and "name" in fields:
                message = fields["message"][0].replace('\r', '').replace('\n', '')
                self.path = 'src/static/done.html'
                # Check if the message is not too long
                if len(message) < 128:
                    self.cb_add_message(MessagingPlugin.Message(fields["name"][0], message, time()))
                else:
                    PrintTraceInUi("Message too long.. Not keeping this one")
                    self.path = 'src/static/ko.html'
            else:
                # Error
                self.path = 'src/static/ko.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        

    class MessagingUiThread:
        active_messages = []
        is_shown = False
        player_window = None
        scroll_thread = None
        frame_messages = None
        maintenance_listbox = None
        active_label_author = ""
        active_label_message = ""
        index_sequence_message = 0

        is_running = False
        params = {}

        def __init__(self, tk_root, params):
            """! Init """
            self.player_window = tk_root
            self.params = params
            self.is_shown = False 
            self.maintenance_listbox = None
            self.scroll_thread = None
            self.is_running = True
            self.frame_messages = tk.Frame(self.player_window, bg=UI_BACKGROUND_COLOR)

            font_size = int(self.player_window.winfo_height() /20);
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
                # By default, compute messages every second
                time_to_wait = 1
                if len(self.active_messages) > 0:
                    # If we display a message, we display it for DISPLAY_TIME seconds
                    time_to_wait = int(self.params[DISPLAY_TIME_PARAM])
                    self.active_messages[self.index_sequence_message].set_not_current_message()
                    self.index_sequence_message = (self.index_sequence_message + 1) % len(self.active_messages)
                    PrintTraceInUi("Index of current message = ", self.index_sequence_message, " Author : ",  
                        self.active_messages[self.index_sequence_message].author, " Message ",
                        self.active_messages[self.index_sequence_message].message)
                    
                    self.active_messages[self.index_sequence_message].set_current_message()
                    font_size = int(self.player_window.winfo_height() /20);
                    PrintTraceInUi("FontSize ", font_size)
                    self.active_label_author.configure(text = self.active_messages[self.index_sequence_message].author, 
                        font=('calibri', font_size, 'bold'))
                    self.active_label_message.configure(text = self.active_messages[self.index_sequence_message].message,
                        font=('calibri', font_size))
                    # Let time to recalculate the message size
                    sleep(0.1)
                    PrintTraceInUi("Message size ", self.active_label_message.winfo_width())
                    PrintTraceInUi("Size of message space ", self.player_window.winfo_width() - self.active_label_author.winfo_width())
                    if self.active_label_message.winfo_width() >= self.player_window.winfo_width() - self.active_label_author.winfo_width():
                        PrintTraceInUi("Message is too long, we need to make it scroll")
                        # A long message needs to be let a longer time
                        time_to_wait = int(self.params[DISPLAY_TIME_LONG_MESSAGE_PARAM])
                        def _scroll_thread():
                            self.active_label_message.configure(anchor=tk.W)
                            current_index_message = self.index_sequence_message
                            message = self.active_messages[self.index_sequence_message].message
                            # First 2 seconds are fixed
                            sleep(2)
                            while self.is_running and current_index_message == self.index_sequence_message:
                                wait = False
                                # removing first char until it fits
                                if self.active_label_message.winfo_width() >= self.player_window.winfo_width() - self.active_label_author.winfo_width():

                                    chunk_message = tk.Label(self.frame_messages,text=message[0:5], font=('calibri', font_size))
                                    chunk_message.place(relx=-1,rely=-1)
                                    sleep(0.05)
                                    width = chunk_message.winfo_width()
                                    PrintTraceInUi(f"Size of chunk {message[0:5]} : {width}")
                                    message = message[6:]
                                    self.active_label_message.configure(text = message)
                                    
                                    while width > 0 and self.is_running:
                                        # Thats a big hack to approximately get the size right.. 
                                        # the padx width is not exactly the true 
                                        self.active_label_message.configure(padx = 10 + 1.07*width)
                                        width = width - 2
                                        sleep(0.01)
                                    chunk_message.destroy()


                                else:
                                    # Then when it fits, wait a bit
                                    wait = True

                                if wait:
                                    sleep(2)
                                    message = self.active_messages[current_index_message].message
                                    self.active_label_message.configure(text = message)
                                    sleep(2)
                                else:
                                    sleep(0.08)
                                self.active_label_message.configure(text = message)
                        if self.scroll_thread is not None:
                            self.scroll_thread.join()
                            self.scroll_thread = None

                        self.scroll_thread = threading.Thread(name="MessageUI Scroll Thread", target=_scroll_thread)
                        self.scroll_thread.start()
                
                
                sleep(time_to_wait)
            #self.frame_messages.destroy()
            if self.scroll_thread is not None:
                self.scroll_thread.join()
                self.scroll_thread = None

        def add_message(self, message):
            """! Adding a message in the dictionary of active message """
            # Remove messages with the same author 
            for active_message in self.active_messages:
                if active_message.author == message.author:
                    active_message.set_inactive()
                    self.active_messages.remove(active_message)

            #self.active_messages = list(filter(lambda active_message: (
            #    active_message.author != message.author), self.active_messages))

            self.active_messages.append(message)
            
            time = datetime.fromtimestamp(
                message.timestamp_activation).time()
            timestamp = "{:02d}".format(time.hour) + ":" + "{:02d}".format(time.minute) + ":" + "{:02d}".format(time.second)
            
            if MESSAGE_FILE_PATH_PARAM in self.params:
                with open(self.params[MESSAGE_FILE_PATH_PARAM], 'a+', encoding='utf-8') as f:
                    f.write(timestamp + " "  +  message.author + " : " + message.message + '\n')
            
            if self.maintenance_listbox is not None:
                self.maintenance_listbox.add_entry(timestamp, message.author, message.message, message.store_active_state_cb, message.store_current_message_cb)

            message.set_active()

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
            self.frame_messages.place(relx=0, rely= -1)

        def stop(self):
            self.is_running = False
        
        def _compute_messages(self):
            # If its been more than 10 minutes, the message disappears from the sequence
            PrintTraceInUi("Recomputing messages..")
            # Change state of messages
            for message in self.active_messages:
                if message.timestamp_activation + int(self.params[DELETE_AFTER_MINUTES_PARAM])*60 < time():
                    PrintTraceInUi(f"Message going inactive ! {message.message}")
                    message.set_inactive()
                    self.active_messages.remove(message)
    
            #self.active_messages = list(filter(lambda message: (
            #    message.timestamp_activation + int(self.params[DELETE_AFTER_MINUTES_PARAM])*60 > time()), self.active_messages))
        
        def subscribe_listbox(self, listbox):
            self.maintenance_listbox = listbox
