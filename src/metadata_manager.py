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
"""! The metadata manager module : reads and open up API
     to the video metadata csv
"""
import csv

from logger import print_trace_in_ui


class MetaDataManager:
    """! Reads and open up API to the video metadata csv

         Parses the metadata csv
         Gives the Player some data about start and end of video playbacks
         and fade in/out options
         Gives also the volume to be set by video in order to have an equalized output
    """
    class MetaDataEntry:
        """! An entry in the metadata list """
        video_name = ""
        timestamp_begin = 0
        timestamp_end = 0
        fade_in = False
        fade_out = False
        artist = None
        song = None

        def __init__(self,
                     video_name,
                     timestamp_begin,
                     timestamp_end,
                     fade_in,
                     fade_out,
                     artist,
                     song):
            """! Initialize the entry """
            self.video_name = video_name
            self.timestamp_begin = timestamp_begin
            self.timestamp_end = timestamp_end
            self.fade_in = fade_in
            self.fade_out = fade_out
            self.artist = artist
            self.song = song

    metadata_list = []
    path = None

    def __init__(self, path=None):
        """! The MetaData manager initializer
            @param path : path the csv metadata file
            @return An instance of a MetaDataManager
        """
        self.metadata_list = []
        if path is not None:
            self.open(path)

    def open(self, path):
        """! Open the metadatafile and fills the metadata list"""
        self.path = path
        with open(path, newline='') as csvfile:
            csvdata = csv.reader(csvfile, delimiter=',')
            for line in csvdata:
                # The csv has to be well formed
                assert len(line) == 7

                # Format the timestamps in seconds
                def get_sec(time_str):
                    minute, second = time_str.split(':')
                    return int(minute) * 60 + int(second)

                self.metadata_list.append(
                    self.MetaDataEntry(video_name=line[0],
                                       timestamp_begin=get_sec(line[1]),
                                       timestamp_end=get_sec(line[2]),
                                       fade_in=line[3] == 'y',
                                       fade_out=line[4] == 'y',
                                       artist=line[5],
                                       song=line[6]))

    def reload(self):
        """! Reloads the metadata info from the file """
        self.metadata_list.clear()
        self.open(self.path)

    def get_metadata(self, video_name):
        """! Get the stored metadata about the video in parameter
            @param video_name : name of the video (as stored in the metadata csv)
            @return a MetaDataEntry structure
        """
        filtered_list = list(filter(lambda meta: (
            meta.video_name == video_name), self.metadata_list))
        if len(filtered_list) == 0:
            print_trace_in_ui(
                "ERROR ! No metadata entries found for video " + video_name)
        else:
            if len(filtered_list) > 1:
                print_trace_in_ui(
                    "WARNING ! Multiple metadata entries for video " +
                    video_name + ". Taking first one")
            return filtered_list[0]

        return None  # Not found
