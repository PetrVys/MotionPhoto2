import re
import os
import struct

from pathlib import Path

import constants as const


def extract_track_number(metadata: str) -> str:
    find = re.search(r"\s*<Track(\d+):StillImageTime>-1<", metadata)
    return find.group(1)


def extract_track_duration(track_number: str, metadata: str) -> str:
    find = re.search(rf"\s*<Track{track_number}:TrackDuration>(\d+\.?\d*)<", metadata)
    track_duration = find.group(1)
    if track_duration is None:
        return -1
    return str(round(float(track_duration) * 1000000))


def read_file(fpath: str) -> bytes:
    with open(fpath, "rb") as f:
        return f.read()


def enrich_fname(fpath: str, enrich: str) -> str:
    p = Path(fpath)
    fname = f"{p.stem}.{enrich}{p.suffix}"
    return os.path.join(p.parent, fname)

