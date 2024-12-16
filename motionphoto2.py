#!/usr/bin/env python3

import argparse
import sys
import os
import exiftool
import logging

from pathlib import Path

from Muxer import Muxer

logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="MotionPhoto2",
        description="Mux HEIC and JPG Live Photos into Google/Samsung Motion Photos",
    )

    parser.add_argument("-ii", "--input-image", help="Input file image (.heic, .jpg)")
    parser.add_argument("-iv", "--input-video", help="Input file video (.mov, .mp4)")
    parser.add_argument("-of", "--output-file", help="Output filename of Live Photos")

    parser.add_argument(
        "-id", "--input-directory", help="Mux all the photos and video in directory"
    )
    parser.add_argument(
        "-od",
        "--output-directory",
        help="Store all the Live Photos into dedicated directory",
    )

    parser.add_argument(
        "-dv",
        "--delete-video",
        action="store_true",
        help="Automatically delete video after muxing",
    )
    parser.add_argument(
        "-kt",
        "--keep-temp",
        action="store_true",
        help="Keep temp file used during muxing",
    )
    parser.add_argument(
        "-nx",
        "--no-xmp",
        action="store_true",
        help="No XMP processing (just glue image and video using Samsung tags)",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite the original image file as output Live Photos",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose muxing")

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively process subdirectories when using input-directory",
    )

    args = parser.parse_args()

    if args.input_directory is not None and (
        args.input_image is not None or args.input_video is not None
    ):
        print("[ERROR] Input directory cannot be use with input-image or input-video")
        sys.exit(1)

    if args.input_directory is None:
        if args.input_image is None or args.input_video is None:
            print("[ERROR] Please provide both input image/video or input directory")
            sys.exit(1)

    if args.output_directory is not None and args.overwrite is True:
        print("[ERROR] Output directory cannot be use overwrite option")
        sys.exit(1)

    if args.output_file is not None and args.overwrite is True:
        print("[ERROR] Output file cannot be use overwrite option")
        sys.exit(1)

    if args.overwrite is True or args.delete_video is True:
        text = f"[WARNING] Make sure to have a backup of your image and/or video file (overwrite={args.overwrite}, delete-video={args.delete_video})"
        confirmation = input(f"{text}\nContinue? [Y/n] ")
        if len(confirmation) > 0 and confirmation[0].lower() == "n":
            sys.exit(1)

    if args.output_directory is not None:
        output_directory = f"{Path(args.output_directory).resolve()}"
        if os.path.exists(output_directory) is False:
            os.mkdir(output_directory)
            
    logger = logging.getLogger("ExifTool")
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    
    with exiftool.ExifToolHelper(
        encoding="utf-8",
        logger=logger if args.verbose is True else None
    ) as et:

        if args.input_directory is not None:
            print(f"Converting files in {args.input_directory}")
            print("=" * 25)
            input_directory = Path(args.input_directory).resolve()
            
            # Get files based on recursive flag
            files = []
            if args.recursive:
                # Recursive mode: walk through all subdirectories
                for root, _, filenames in os.walk(input_directory):
                    for filename in filenames:
                        full_path = Path(root) / filename
                        rel_path = full_path.relative_to(input_directory)
                        files.append(str(rel_path))
            else:
                # Non-recursive mode: only process files in the specified directory
                for filename in os.listdir(input_directory):
                    if os.path.isfile(input_directory / filename):
                        files.append(filename)
            
            # Filter videos and images while preserving relative paths
            videos = [
                f for f in files
                if Path(f).suffix.lower() in [".mp4", ".mov"]
            ]
            
            images = [
                f for f in files
                if Path(f).suffix.lower() in [".heic", ".heif", ".avif", ".jpg", ".jpeg"]
            ]
            
            for image in images:
                image_path = Path(image)
                fname = str(image_path.with_suffix(''))
                
                # Check for both regular video filename and one with _HEVC suffix
                possible_video_names = [
                    fname,  # Original name
                    f"{fname}_HEVC"  # Name with _HEVC suffix
                ]
                
                for video_name in possible_video_names:
                    for ext in [".mp4", ".mov", ".MP4", ".MOV"]:
                        video_fname = f"{Path(video_name).with_suffix(ext)}"
                        if video_fname in videos:
                            video = videos.pop(videos.index(video_fname))

                            # Construct full paths for input files
                            input_image = input_directory / image
                            input_video = input_directory / video
                            
                            # Handle output directory structure
                            output_subdirectory = args.output_directory                   
                            if output_subdirectory is not None:
                                # Preserve directory structure in output
                                output_subdirectory = Path(output_subdirectory) / image_path.parent
                                output_subdirectory = output_subdirectory.resolve()
                                if not output_subdirectory.exists():
                                    output_subdirectory.mkdir(parents=True, exist_ok=True)
                            
                            Muxer(
                                image_fpath=str(input_image),
                                video_fpath=str(input_video),
                                exiftool=et,
                                output_directory=str(output_subdirectory) if output_subdirectory else None,
                                delete_video=args.delete_video,
                                delete_temp=not args.keep_temp,
                                overwrite=args.overwrite,
                                no_xmp=args.no_xmp,
                                verbose=args.verbose,
                            ).mux()
                            print("=" * 25)
                            break
                    else:
                        continue
                    break
        else:
            Muxer(
                image_fpath=args.input_image,
                video_fpath=args.input_video,
                exiftool=et,
                output_fpath=args.output_file,
                output_directory=args.output_directory,
                delete_video=args.delete_video,
                delete_temp=not args.keep_temp,
                overwrite=args.overwrite,
                no_xmp=args.no_xmp,
                verbose=args.verbose,
            ).mux()
