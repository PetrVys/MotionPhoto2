#!/usr/bin/env python3

import argparse
import filecmp
import itertools
import shutil
import sys
import os
import exiftool
import logging

from pathlib import Path
from gooey import GooeyParser

from Muxer import Muxer
from utils import is_motion_photo, extract_video_from_image, input_output_binary_compare

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
        "Process a Directory",
        gooey_options={'columns':4}
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
        help="Recursively process subdirectories",
        gooey_options={'initial_value':True}
    )

    dir_group.add_argument(
        "-em", 
        "--exif-match",
        metavar="Match by EXIF",
        action="store_true",
        help="Match files by Live Photo metadata",
        gooey_options={'initial_value':True}
    )

    dir_group.add_argument(
        "-cu",
        "--copy-unmuxed",
        metavar="Copy Unmuxed",
        action="store_true",
        help="Copy files that are not Live Photos",
    )

    dir_group.add_argument(
        "-od",
        "--output-directory",
        metavar="Output Directory",
        help="Directory where to save the resulting Motion Photos",
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
        "-im",
        "--incremental-mode",
        metavar="Incremental Mode",
        action="store_true",
        help="Skip muxing if output file is already a motion photo.",
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

    if args.output_directory is None and args.copy_unmuxed is True:
        print("[ERROR] Copy unmuxed cannot be used without output directory")
        sys.exit(1)

    if args.output_directory is None and args.incremental_mode is True:
        print("[ERROR] Incremental mode cannot be used without output directory")
        sys.exit(1)

    if args.output_directory is not None and args.overwrite is True:
        print("[ERROR] Output directory cannot be use overwrite option")
        sys.exit(1)

    if args.output_file is not None and args.overwrite is True:
        print("[ERROR] Output file cannot be use overwrite option")
        sys.exit(1)

    if args.copy_unmuxed is not None and args.overwrite is True:
        print("[ERROR] Copy Unmuxed cannot be used with overwrite option")
        sys.exit(1)

    if args.copy_unmuxed is not None and args.delete_video is True:
        print("[ERROR] Copy Unmuxed cannot be used with delete-video option")
        sys.exit(1)

    if args.output_directory is not None:
        output_directory = f"{Path(args.output_directory).resolve()}"
        if os.path.exists(output_directory) is False:
            os.mkdir(output_directory)
        elif os.path.isfile(output_directory):
            print("[ERROR] Output directory cannot be a file")
            sys.exit(1)
        elif args.copy_unmuxed is not None:
            input_directory = f"{Path(args.input_directory).resolve()}"
            if os.path.samefile(input_directory, output_directory): # Input directory and output directory cannot be same if copying unmuxed files
                print("[ERROR] Output directory cannot be the same as input directory")
            
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
            
            unsupported = [
                f for f in files
                if Path(f).suffix.lower() not in [".mp4", ".mov", ".heic", ".heif", ".avif", ".jpg", ".jpeg"]
            ]

            unmatched_images = []
            
            if not args.exif_match: # match by file name
                i = 0
                for image in images:
                    i += 1
                    image_path = Path(image)
                    fname = str(image_path.with_suffix(''))

                    # Check if source image is already a motion photo
                    if is_motion_photo(input_directory / image, et):
                        print(f"Input {image} is already a motion photo, skipping muxing...")
                        if args.copy_unmuxed:
                            unmatched_images.append(image)
                        continue
                    
                    for ext in [".mp4", ".mov", ".MP4", ".MOV"]:
                        video_fname = fname + ext
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

                            if args.incremental_mode:
                                output_image_path = output_subdirectory / image_path.name
                                if os.path.exists(output_image_path) and input_output_binary_compare(input_video,output_image_path):
                                    print(f"Destination {image} is already a motion photo, skipping...")
                                    break
                            
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
                        print(f"No matching video found for {image}")
                        if args.copy_unmuxed:
                            unmatched_images.append(image)
                        
            else: # match by exif
                image_paths = [input_directory / img for img in images]
                video_paths = [input_directory / vid for vid in videos]
                print("Running in EXIF matching mode.")
                print("Getting metadata for images, please wait...")
                image_metadatas = et.get_metadata([str(p) for p in image_paths])
                print("Getting metadata for videos, please wait...")
                video_metadatas = et.get_metadata([str(p) for p in video_paths])
                
                # Map content identifiers to video relative paths
                content_id_to_video = {}
                for meta, vid in zip(video_metadatas, videos):
                    content_id = meta.get('QuickTime:ContentIdentifier')
                    if content_id:
                        content_id_to_video[content_id.strip()] = vid
                        if args.verbose:
                            print(f"[DEBUG] Mapped video {vid} to ContentIdentifier: {content_id}")
                
                # Match images to videos
                i = 0
                for img, img_meta in zip(images, image_metadatas):

                    # Check if source image is already a motion photo
                    if is_motion_photo(input_directory / img, et):
                        print(f"Input {img} is already a motion photo, skipping muxing...")
                        if args.copy_unmuxed:
                            unmatched_images.append(img)
                        continue

                    i += 1
                    content_id = img_meta.get('MakerNotes:ContentIdentifier')
                    if args.verbose and content_id:
                        print(f"[DEBUG] Image {img} has ContentIdentifier: {content_id}")
                    if content_id and content_id.strip() in content_id_to_video:
                        print(f"=========================[{i}/{len(images)}]")
                        video = content_id_to_video[content_id.strip()]

                        if args.copy_unmuxed:
                            videos.remove(video)
                        
                        # Construct full paths for input files
                        input_image = input_directory / img
                        input_video = input_directory / video
                        
                        # Handle output directory structure
                        output_subdirectory = args.output_directory
                        if output_subdirectory is not None:
                            image_path = Path(img)
                            output_subdirectory = Path(output_subdirectory) / image_path.parent
                            output_subdirectory = output_subdirectory.resolve()
                            if not output_subdirectory.exists():
                                output_subdirectory.mkdir(parents=True, exist_ok=True)

                        if args.incremental_mode:
                            # Try matching using Content id
                            output_image_path = output_subdirectory / image_path.name
                            if os.path.exists(output_image_path):
                                output_metadata = et.get_metadata(output_image_path)[0]
                                output_image_content_id = output_metadata.get('MakerNotes:ContentIdentifier')
                                output_video_data_from_image = extract_video_from_image(output_image_path, et)

                                # Check if content IDs match
                                if all((output_video_data_from_image,
                                        output_image_content_id,
                                        output_video_data_from_image.find(output_image_content_id.strip().encode()) != -1,
                                        output_video_data_from_image.find(content_id.strip().encode()) != -1)):
                                        if args.verbose:
                                            print(f"[DEBUG] ContentIdentifier '{content_id.strip()}' of the source {input_image} and {output_image_path} destination matches")
                                        print(f"Destination {img} as it is already a motion photo, skipping...")
                                        continue
                                else:
                                    # Do binary comparison to check input and output
                                    if input_output_binary_compare(input_video,output_image_path):
                                        print(f"Destination {img} is already a motion photo, skipping...")
                                        continue

                        print("Muxer running.....................................")
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
                    else:
                        print(f"No matching video found for {img}")
                        if args.copy_unmuxed:
                            unmatched_images.append(img)

            # Copy unmuxed images and videos while preserving the directory structure
            if args.copy_unmuxed:
                print("=" * 25)
                print("Copying unmuxed files...")
                for file in itertools.chain(unmatched_images, videos, unsupported):
                    # Handle output directory structure
                    output_subdirectory = args.output_directory
                    if output_subdirectory is not None:
                        file_path = Path(file)
                        output_subdirectory = Path(output_subdirectory) / file_path.parent
                        output_subdirectory = output_subdirectory.resolve()
                        if not output_subdirectory.exists():
                            output_subdirectory.mkdir(parents=True, exist_ok=True)
                    print(f"Copying {file} to {output_subdirectory}")
                    if os.path.exists(output_subdirectory / file_path.name) and filecmp.cmp(input_directory / file, output_subdirectory / file_path.name):
                        if args.verbose:
                            print(f"[DEBUG][WARNING] File {file} already exists in output directory, skipping..." )
                        continue
                    shutil.copy2(input_directory / file, output_subdirectory)
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
