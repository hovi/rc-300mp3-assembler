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


destination = "destination/"
source = "test_data/"
# uncomment when converting directly from usb-connected looper, but copy locally first is safer
source = "/Volumes/BOSS_RC-300/ROLAND/WAVE/"

tracksettings = {
    "t8": {
        "source": source,
        "destination": destination,
        "track_groups": [
            {
                "longest": 'm8t2',
                "tracks": [
                    {
                        "track_index": 1,
                        "memory_index": 8,
                        "loop": True,
                        "volume": 1,
                        "disable": False
                    }
                    ,
                    {
                        "track_index": 2,
                        "memory_index": 8,
                        "loop": False,
                        "volume": 1,
                        "disable": False,
                    }
                    ,
                    {
                        "track_index": 3,
                        "memory_index": 8,
                        "loop": True,
                        "volume": 1,
                        "disable": False,
                    }
                ]
            }
        ],
    },
    "cryin_guitar": {
        "source": source,
        "destination": destination,
        "track_groups": [
            {
                "longest": 'm6t3',
                "tracks": [
                    {
                        "track_index": 1,
                        "memory_index": 6,
                        "loop": True,
                        "volume": 1,
                        "disable": False
                    }
                    ,
                    {
                        "track_index": 2,
                        "memory_index": 6,
                        "loop": True,
                        "volume": 1,
                        "disable": False,
                    }
                    ,
                    {
                        "track_index": 3,
                        "memory_index": 6,
                        "loop": False,
                        "volume": 1,
                        "disable": False,
                    }
                ]
            }
        ],
    }
}


class Track:
    def __init__(self, settings):
        self.valid = True
        self.memory_index = settings["memory_index"]
        self.track_index = settings["track_index"]
        self.settings = settings
        self.disabled = "disable" in settings and settings["disable"]
        self.path = self.original_path()
        self.index = "m" + str(self.memory_index) + "t" + str(self.track_index)

    def original_path(self):
        self.track_dir_name = str(self.memory_index).zfill(3) + "_" + str(self.track_index)
        self.track_relative_path = os.path.join(self.track_dir_name, self.track_dir_name + ".wav")
        path = os.path.join(source, self.track_relative_path)
        if not os.path.exists(path):
            self.valid = False
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
        # track_loop = track[:-4] + "x" + str(loops) + "_loop.wav"
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
    def __init__(self, settings):
        self.settings = settings
        # TODO: add more for each group
        self.tracks = self.create_tracks(settings)
        print self.tracks

    def create_tracks(self, settings):
        tracks = OrderedDict()
        for track_settings in settings["tracks"]:
            if not track_settings["disable"]:
                track = Track(track_settings)
                if track.valid:
                    tracks[track.index] = track
                else:
                    print "Track not valid: " + track.index
        return tracks

    def max_length(self):
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

    def merge(self, destination, output_file="output.mp3"):
        final_path = os.path.join(destination, output_file)
        if os.path.exists(final_path):
            raise ValueError("File exists: " + final_path)
        self.longest_first()
        tracks = self.tracks
        args = ["ffmpeg", "-y"]
        for track_index in tracks:
            args.extend(["-i", tracks[track_index].path])
        args.extend(["-filter_complex", "amix=duration=first:inputs=" + str(len(tracks)), "-f", "mp3"])
        args.extend([final_path])
        run_args(args)

    def longest_first(self):
        tracks = self.tracks
        new_tracks = OrderedDict()
        longest_index = self.settings["longest"]
        new_tracks[longest_index] = tracks[longest_index]
        for track_index in tracks:
            track = tracks[track_index]
            new_tracks[track_index] = track
        self.tracks = new_tracks
        return self.tracks

    def process(self, max_length):
        for track in self.tracks.values():
            track.process(max_length)

    def __unicode__(self):
        return str(self.tracks.values())

    def __str__(self):
        return self.__unicode__()


def convert(settings, name, suffix):
    tracks = Tracks(settings["track_groups"][0])
    max_track, max_length, max_index = tracks.max_length()
    print tracks.tracks
    tracks.process(max_length)
    tracks.merge(settings["destination"], name + suffix + "_merge.mp3")


def main():
    if len(sys.argv) < 1:
        print "Please specify settings you want to use. Ex:"
        print "python maketrack.py t8"
        return
    settings_arg = "t8"
    suffix = ""
    if len(sys.argv) > 1:
        settings_arg = sys.argv[1]
    if len(sys.argv) > 2:
        suffix = sys.argv[2]

    settings = tracksettings[settings_arg]
    convert(settings, settings_arg, suffix)


if __name__ == "__main__":
    main()
