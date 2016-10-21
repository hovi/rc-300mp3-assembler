# rc-300mp3-assembler
Assemble mp3 from rc-300 looper wave data.

Run using (cryin_guitar settings key, _v2 optinal file name suffix):
```bash
python nmaketrack.py cryin_guitar _v2
```

Example settings:
```python
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
```
