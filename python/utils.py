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


def merge_bytes(
    image_bytes: bytes, video_bytes: bytes, image_type: str = "heic"
) -> bytes:
    image_size = len(image_bytes)
    video_size = len(video_bytes)
    if image_type == 'heic':
        # 8 - mpvd box size, 76 - size of full footer ($samsungTailStart + $videoOffset + $videoSize + $samsungTailEnd)
        mpvd_size = video_size + const.MPVD_BOX_SIZE + const.SAMSUNG_TAIL_SIZE
        # 8 is the size of mpvd box
        video_offset = image_size + const.MPVD_BOX_SIZE
    else:
        mpvd_size = 0
        video_offset = image_size

    mpvd_size_bytes = struct.pack(">i", mpvd_size)
    video_offset_bytes = struct.pack( ">i", video_offset)
    video_size_bytes = struct.pack(">i", video_size)

    if image_type == "heic":
        image_bytes += mpvd_size_bytes
        image_bytes += const.MPVD_BOX_NAME

    image_bytes += video_bytes
    image_bytes += const.SAMSUNG_TAIL_START
    image_bytes += video_offset_bytes
    image_bytes += video_size_bytes
    image_bytes += const.SAMSUNG_TAIL_END
    return image_bytes
