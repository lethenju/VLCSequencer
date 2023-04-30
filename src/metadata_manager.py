import csv

from logger import PrintTraceInUi

class MetaDataManager:
    """! Reads and open up API to the video metadata csv

         Parses the metadata csv
         Gives the Player some data about start and end of video playbacks
         and fade in/out options
         Gives also the volume to be set by video in order to have an equalized output
    """
    class MetaDataEntry:
        video_name = ""
        timestamp_begin = 0
        timestamp_end = 0
        fade_in = False
        fade_out = False
        artist = None
        song = None

        def __init__(self, video_name, timestamp_begin, timestamp_end, fade_in, fade_out, artist, song):
            self.video_name = video_name
            self.timestamp_begin = timestamp_begin
            self.timestamp_end = timestamp_end
            self.fade_in = fade_in
            self.fade_out = fade_out
            self.artist = artist
            self.song = song

    metadata_list = []

    def __init__(self, path):
        """! The MetaData manager initializer
            @param path : path the csv metadata file 
            @return An instance of a MetaDataManager
        """
        with open(path, newline='') as csvfile:
            csvdata = csv.reader(csvfile, delimiter=',')
            for line in csvdata:
                # The csv has to be well formed
                assert (len(line) == 7)

                # Format the timestamps in seconds
                def get_sec(time_str):
                    m, s = time_str.split(':')
                    return int(m) * 60 + int(s)

                self.metadata_list.append(
                    self.MetaDataEntry(video_name=line[0],
                                       timestamp_begin=get_sec(line[1]),
                                       timestamp_end=get_sec(line[2]),
                                       fade_in=line[3] == 'y',
                                       fade_out=line[4] == 'y',
                                       artist=line[5],
                                       song=line[6])
                )

    def get_metadata(self, video_name):
        """! Get the stored metadata about the video in parameter 
            @param video_name : name of the video (as stored in the metadata csv)
            @return a MetaDataEntry structure
        """
        it = list(filter(lambda meta: (
            meta.video_name == video_name), self.metadata_list))
        if len(it) == 0:
            PrintTraceInUi(
                "ERROR ! No metadata entries found for video " + video_name)
        else:
            if len(it) > 1:
                PrintTraceInUi("WARNING ! Multiple metadata entries for video " +
                               video_name + ". Taking first one")
            return it[0]