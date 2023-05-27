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

import tkinter as tk
from tkinter import filedialog
import os
import sys
import argparse
import vlc

# Application related imports
from colors import UI_BACKGROUND_COLOR, \
                   UI_BLOCK_NORMAL_VIDEO_COLOR, \
                   UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR
from metadata_manager import MetaDataManager
from plugin_manager import PluginManager
from ui_player import UiPlayer
from sequencer import UiSequenceManager, MainSequencer


class MainManager:
    """! Main manager of the program

         Initialize and control the different application components
    """
    sequencer = None
    root = None
    metadata_button = None
    metadata_path = ""
    sequence_button = None
    sequence_path = ""

    def __init__(self, sequence_file, metadata_file, launch_now):
        """! The main manager initializer, handles the welcome screen to
            select a sequence file and metadata
        """
        self.sequence_path = sequence_file
        self.metadata_path = metadata_file
        self.root = tk.Tk()

        if launch_now:
            if not os.path.isfile(self.sequence_path):
                print("ERROR ", self.sequence_path, " IS NOT A VALID FILE")
                sys.exit(1)
            if not os.path.isfile(self.metadata_path):
                print("ERROR ", self.metadata_path, " IS NOT A VALID FILE")
                sys.exit(1)
            self.start_ui()
        else:
            title_view = tk.Frame(
                self.root,
                width=400,
                height=300,
                background=UI_BACKGROUND_COLOR)
            title_view.pack(side=tk.TOP,  fill=tk.BOTH)

            lbl = tk.Label(title_view, font=('calibri', 80, 'bold'),
                           text="VLCSequencer", background=UI_BACKGROUND_COLOR, foreground='white')
            lbl.pack(side=tk.TOP,  fill=tk.BOTH, pady=50)

            lbl = tk.Label(title_view,
                           font=('calibri', 20),
                           text="Place this window where you want " +
                                "the videos to be played",
                           background=UI_BACKGROUND_COLOR,
                           foreground=UI_BLOCK_NORMAL_VIDEO_COLOR)
            lbl.pack(side=tk.TOP,  fill=tk.BOTH, pady=50)

            buttons_frame = tk.Frame(
                self.root,
                width=400,
                height=300,
                pady=10,
                background=UI_BACKGROUND_COLOR)
            buttons_frame.pack(side=tk.BOTTOM,  fill=tk.BOTH, expand=1)

            def select_metadata_file():
                self.metadata_path = filedialog.askopenfilename(
                    title='Select Metadata File',
                    filetypes=[('Csv files', '*.csv')])

                if os.path.isfile(self.metadata_path):
                    self.metadata_button.configure(
                        bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)

            def select_sequence_file():
                self.sequence_path = filedialog.askopenfilename(
                    title='Select Sequence File',
                    filetypes=[('Xml files', '*.xml')])
                if os.path.isfile(self.sequence_path):
                    self.sequence_button.configure(
                        bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
                    start_button.configure(state=tk.NORMAL)

            self.metadata_button = tk.Button(
                buttons_frame,
                text='Select Metadata file',
                command=select_metadata_file,
                padx=10, pady=10, font=('calibri', 12),
                fg="white",
                bg=UI_BACKGROUND_COLOR
            )
            self.sequence_button = tk.Button(
                buttons_frame,
                text='Select Sequence file',
                command=select_sequence_file,
                padx=10, pady=10, font=('calibri', 12),
                fg="white",
                bg=UI_BACKGROUND_COLOR
            )

            start_button = tk.Button(
                buttons_frame, text="Start", command=self.start_ui,
                padx=10, pady=10, font=('calibri', 12),
                fg="white",
                bg=UI_BACKGROUND_COLOR,
                state=tk.DISABLED)

            start_button.pack(side=tk.BOTTOM,  fill=tk.BOTH)
            self.metadata_button.pack(side=tk.BOTTOM,  fill=tk.BOTH)
            self.sequence_button.pack(side=tk.BOTTOM,  fill=tk.BOTH)

            # if the paths are already filled by the command line
            if self.metadata_path is not None and \
               os.path.isfile(self.metadata_path):
                self.metadata_button.configure(
                    bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            if self.sequence_path is not None \
               and os.path.isfile(self.sequence_path):
                self.sequence_button.configure(
                    bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
                start_button.configure(state=tk.NORMAL)

    def start_ui(self):
        """! Start the sequence and player UI """
        # Directsound allow audio crossfading : each player has an individual sound
        instance = vlc.Instance(['--aout=directsound', '--quiet', '--no-xlib'])
        assert instance is not None

        # Clean up window for letting space for playback
        for child in self.root.winfo_children():
            child.destroy()

        metadata_manager = None
        if os.path.isfile(self.metadata_path):
            metadata_manager = MetaDataManager(path=self.metadata_path)

        plugin_manager = PluginManager()

        player = UiPlayer(tkroot=self.root,
                          vlc_instance=instance,
                          metadata_manager=metadata_manager,
                          plugin_manager=plugin_manager)
        self.sequence_manager = UiSequenceManager(
            tkroot=self.root,
            vlc_instance=instance,
            ui_player=player,
            path=self.sequence_path,
            metadata_manager=metadata_manager,
            plugin_manager=plugin_manager)
        self.sequence_manager.load_sequence()

        self.sequencer = MainSequencer(
            ui_player=player, ui_sequencer=self.sequence_manager)
        self.sequencer.launch_sequencer()

        self.sequence_manager.set_main_sequencer_stop_cb(self.sequencer.kill)

        def on_close():
            self.sequence_manager.kill()
            self.sequencer.kill()

        self.root.protocol("WM_DELETE_WINDOW", on_close)

    def main_loop(self):
        """! mainloop of the program
        """
        self.root.mainloop()


# Prevents this code to be runned if loaded as a module
if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="VLCSequencer")
    parser.add_argument('-s',
                        '--sequence',
                        help="Path of the sequence file to use",
                        action="store")
    parser.add_argument('-m',
                        '--metadata',
                        help="Path of the metadata file to use",
                        action="store")
    parser.add_argument('-l',
                        '--launch',
                        help="Set if you want to launch directly without\
                              going through the main menu",
                        action="store_true")
    args = parser.parse_args()

    MainManager(sequence_file=args.sequence,
                metadata_file=args.metadata,
                launch_now=args.launch).main_loop()
