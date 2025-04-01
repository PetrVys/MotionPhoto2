import logging
import re
import os
import struct

from pathlib import Path
import exiftool

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

def is_motion_photo(fpath: str, verbose: bool = False) -> bool:
    video_in_image = extract_video_from_image(fpath, verbose)

    # Check if the data received is actually a video file
    if video_in_image and  verify_video_in_image(video_in_image):
                return True
    return False

def verify_video_in_image(video_in_image: bytes) -> bool :
    if video_in_image:
        for sig in const.VIDEO_SIGNATURE["MOV"] + const.VIDEO_SIGNATURE["MP4"]:
            if video_in_image.find(sig, 0, 15):
                return  True
    return False


def extract_video_from_image(fpath: str, verbose: bool = False) -> bytes:
    logger = logging.getLogger("ExifTool")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    with exiftool.ExifToolHelper(
            encoding="utf-8",
            logger=logger if verbose is True else None
    ) as et:
        # Check using GCamera headers
        video_in_image = et.execute("-b",
                                    "-MotionPhotoVideo",
                                    fpath,
                                    raw_bytes=True)

        # If not then check using samsung headers
        if not video_in_image:
            video_in_image = et.execute("-b",
                                        "-EmbeddedVideoFile",
                                        fpath,
                                        raw_bytes=True)

        return video_in_image

def input_output_binary_compare(input_image: str, input_video: str, output_image: str) -> bool:
    if all((os.path.exists(input_image), os.path.exists(input_video), os.path.exists(output_image))):
        try:
            with open(input_image, "rb") as i_img:
                input_image_data = i_img.read()
                with open(input_video, "rb") as i_vid:
                    input_video_data = i_vid.read()
                    with open(output_image, "rb") as o_img:
                        output_image_data = o_img.read()
                        if output_image_data.find(input_image_data) and output_image_data.find(input_video_data):
                            return True
        except:
            pass
    return False
