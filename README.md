# rc-300mp3-assembler
Assemble mp3 from rc-300 looper wave data.

Example settings:
```python
    {
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
        "longest": "2", # will be used for final track length
    }
```
