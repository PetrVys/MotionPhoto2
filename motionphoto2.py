#!/usr/bin/env python3

import argparse
import sys
import os
import exiftool
import logging

from pathlib import Path
from gooey import GooeyParser

from Muxer import Muxer

logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

def main():    
    parser = GooeyParser(
        prog="MotionPhoto2",
        description="Mux HEIC and JPG Live Photos into Google/Samsung Motion Photos",
    )
    
    dir_group = parser.add_argument_group(
        "Process a Directory"
    )

    dir_group.add_argument(
        "-id", 
        "--input-directory",
        metavar="Input Directory",
        help="Mux all the photos and videos in a directory",
        widget='DirChooser',
        gooey_options={'full_width':True}
    )
    
    dir_group.add_argument(
        "-r",
        "--recursive",
        metavar="Recursive",
        action="store_true",
        help="Recursively process subdirectories in input_directory",
        gooey_options={'initial_value':True}
    )

    dir_group.add_argument(
        "-od",
        "--output-directory",
        metavar="Output Directory",
        help="Directory where to save the resulting Live Photos",
        widget='DirChooser',
        gooey_options={'full_width':True}
    )

    settings_group = parser.add_argument_group(
        "Settings",
        gooey_options={'columns':4}
    )

    settings_group.add_argument(
        "-dv",
        "--delete-video",
        metavar="Delete Video",
        action="store_true",
        help="Delete video after muxing",
    )
    
    settings_group.add_argument(
        "-o",
        "--overwrite",
        metavar="Overwrite",
        action="store_true",
        help="Overwrite the original image",
    )
    
    settings_group.add_argument(
        "-kt",
        "--keep-temp",
        metavar="Keep Temp",
        action="store_true",
        help="Keep muxing temp files",
    )
    
    settings_group.add_argument(
        "-v", 
        "--verbose",
        metavar="Verbose",
        action="store_true", 
        help="Verbose output"
    )

    file_group = parser.add_argument_group(
        "Process a Single File"
    )

    file_group.add_argument(
        "-ii",
        "--input-image",
        metavar="Input Image",
        help="Input file image (.heic, .jpg)",
        widget='FileChooser',
        gooey_options={
            'wildcard':
                "HEIC file|*.heic|"
                "HEIF file|*.heif|"
                "JPG file|*.jpg|"
                "All files (*.*)|*.*",
            'message': "Select image file"
        }
    )
        
    file_group.add_argument(
        "-iv",
        "--input-video",
        metavar="Input Video",
        help="Input file video (.mov, .mp4)", 
        widget='FileChooser',
        gooey_options={
            'wildcard':
                "MOV file|*.mov|"
                "MP4 file|*.mp4|"
                "All files (*.*)|*.*",
            'message': "Select video file"
        }
    )

    file_group.add_argument(
        "-of", 
        "--output-file",
        metavar="Output File",
        help="Output Live Photo filename",
        widget='FileSaver',
        gooey_options={
            'wildcard':
                "HEIC file|*.heic|"
                "HEIF file|*.heif|"
                "JPG file|*.jpg|"
                "All files (*.*)|*.*",
            'message': "Target image file"
        }
    )

    file_group.add_argument(
        "-nx",
        "--no-xmp",
        metavar="No XMP",
        action="store_true",
        help="No XMP processing (just glue image and video using Samsung tags)",
        gooey_options={'visible':False}
    )

    file_group.add_argument(
        "-ts",
        "--time-offset",
        metavar="Time offset (seconds)",
        help=("Manually set the key-frame's time offset, "
              "instead of using the XMP value from the input video. "
              "Only work with single file processing"),
        type=float,
        default=None,
        action="store",
        gooey_options={'visible':False},
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
            
            i = 0
            for image in images:
                i += 1
                image_path = Path(image)
                fname = str(image_path.with_suffix(''))
                
                # Check for both regular video filename and one with _HEVC suffix
                possible_video_names = [
                    fname,  # Original name
                    f"{fname}_HEVC"  # Name with _HEVC suffix
                ]
                
                for video_name in possible_video_names:
                    for ext in [".mp4", ".mov", ".MP4", ".MOV"]:
                        video_fname = video_name + ext
                        if video_fname in videos:
                            print(f"=========================[{i}/{len(images)}]")
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
                            break
                    else:
                        continue
                    break
            print("=" * 25)
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
                time_offset_sec=args.time_offset,
                verbose=args.verbose,
            ).mux()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        from gooey import Gooey
        main = Gooey(program_name='MotionPhoto2',
                     default_size=(1100, 820),
                     progress_regex=r"^=+\[(\d+)/(\d+)]$",
                     progress_expr="x[0] / x[1] * 100",
                     show_restart_button=False,
                    )(main)
    # Gooey reruns the script with this parameter for the actual execution.
    # Since we don't use decorator to enable commandline use, remove this parameter
    # and just run the main when in commandline mode.
    if '--ignore-gooey' in sys.argv:
        sys.argv.remove('--ignore-gooey')
    main()