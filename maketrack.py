import sys
import subprocess
import os
import re
from collections import OrderedDict
from tempfile import NamedTemporaryFile

def get_audio_info(audio_path):
    # args = ["ffprobe", "-show_entries", "format=duration", "-i", audio_path]
    args = ["ffprobe", "-show_streams", "-i", audio_path]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return {
        "length": float(re.search("duration=(\d+\.\d+)", output).group(1)),
        "sample_rate": int(re.search("sample_rate=(\d+)", output).group(1))
    }

def run_args(args):
    process = subprocess.Popen(args, stdout=subprocess.PIPE, close_fds=True)
    out, err = process.communicate()
    if process.poll() != 0:
        print("Error while processing ffmpeg command: " + str(args))
        print(out)
        print(err)

        

tracksettings = {
    "default": {
        "tracks": {
            "1": {
                "loop": True,
                "volume": 1,
                "disable": False
            },
            "2": {
                "loop": False,
                "loop_count": None,
                "volume": 1,
                "disable": False,
            },
            "3": {
                "loop": False,
                "loop_count": None,
                "volume": 1,
                "disable": True,
            },
        },
        "longest": "2",
    }
}

# uncomment when converting directly from usb-connected looper, but copy locally first is safer
# source = "/Volumes/BOSS_RC-300/ROLAND/WAVE/"
source = "test_data/"
destination = "destination/"


class Track:
    def __init__(self, memory_index, track_index, settings):
        self.memory_index = memory_index
        self.track_index = track_index
        self.settings = settings
        self.disabled =  "disable" in settings and settings["disable"]
        self.path = self.original_path()
        
    def original_path(self):
        self.track_dir_name = str(self.memory_index).zfill(3) + "_" + str(self.track_index)
        self.track_relative_path = os.path.join(self.track_dir_name, self.track_dir_name + ".wav")
        path = os.path.join(source, self.track_relative_path)
        if not os.path.exists(path):
            return None
        return path
    
    def info(self):
        return get_audio_info(self.path)
    
    def process(self, max_length):
        if "loop" in self.settings and self.settings["loop"]:
            self.make_loop(max_length)
        if "volume" in self.settings and self.settings["volume"] != 1:
            self.adjust_volume(self.settings["volume"])
            
    def adjust_volume(self, volume):
        new_file = NamedTemporaryFile(delete=False, prefix=self.track_dir_name, suffix=".wav")
        new_file.close()
        args = ["ffmpeg", "-y", "-i", self.path, "-af", "volume=" + str(volume), new_file.name]
        run_args(args)
        self.path = new_file.name
        return new_file.name
    
    def make_loop(self, max_length):
        track_info = self.info()
        length = track_info["length"]
        loops = int(max_length / length) + 1
        #track_loop = track[:-4] + "x" + str(loops) + "_loop.wav"
        new_file = NamedTemporaryFile(delete=False, prefix=self.track_dir_name, suffix=".wav")
        new_file.close()
        args = ["sox", self.path, new_file.name, "repeat", str(loops)]
        run_args(args)
        self.path = new_file.name
        return new_file.name
    
    def __unicode__(self):
        if not self.track_relative_path:
            self.original_path()
        return self.track_relative_path
    
    def __repr__(self):
        return self.__unicode__()
    
    
class Tracks:
    def __init__(self, memory_index, settings):
        self.settings = settings
        self.memory_index = memory_index
        self.tracks = self.create_tracks(memory_index, settings)    

    def create_tracks(self, memory_index, settings):
        tracks = OrderedDict()
        for track_index in range(1, 4):
            track = Track(memory_index, track_index, settings["tracks"][str(track_index)])
            if track is not None and track.path is not None:
                tracks[str(track_index)] = track
        return tracks

    def get_longest(self):
        tracks = self.tracks
        max_length = 0
        max_track = None
        max_index = None
        for track_index in tracks:
            track = tracks[track_index]
            track_info = get_audio_info(track.path)
            if track_info["length"] > max_length:
                max_length = track_info["length"]
                max_track = track
                max_index = track_index

        return max_track, max_length, max_index

    def merge(self, output_file="output.mp3"):
        self.longest_first()
        tracks = self.tracks
        args = ["ffmpeg", "-y"]
        for track_index in tracks:
            args.extend(["-i", tracks[track_index].path])    
        args.extend(["-filter_complex", "amix=duration=first:inputs=" + str(len(tracks)), "-f", "mp3"])
        args.extend([os.path.join(destination, output_file)])
        run_args(args)
        
    def longest_first(self):
        tracks = self.tracks
        new_tracks = OrderedDict()
        longest_index = self.settings["longest"]
        new_tracks[longest_index] = tracks[longest_index]
        for track_index in tracks:
            new_tracks[track_index] = tracks[track_index]
        self.tracks = new_tracks
        return self.tracks
    
    def process(self, max_length):
        settings = self.settings
        tracks = self.tracks
        for track_index in settings["tracks"]:
            if track_index in tracks:
                track = tracks[track_index]
                if track.disabled:
                    del tracks[track_index]
                else:
                    track.process(max_length)
        
    def __unicode__(self):
        return str(self.tracks.values())
    
    def __str__(self):
        return self.__unicode__()

def convert(memory_index, settings):
    tracks = Tracks(memory_index, settings)
    max_track, max_length, max_index = tracks.get_longest()
    tracks.process(max_length)
    tracks.merge(str(memory_index).zfill(3) + "_merge.mp3")
    
def main():
    if len(sys.argv) < 2:
        print "Please specify track you want to use. Ex:"
        print "python maketrack.py 7"
        return
    memory_index = int(sys.argv[1])
    settings = tracksettings["default"]
    if len(sys.argv) > 2:
        settings = tracksettings[sys.argv[2]]
    convert(memory_index, settings)
        
if __name__ == "__main__":
    main()