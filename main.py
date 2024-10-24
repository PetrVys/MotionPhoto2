import argparse
import sys
import os

from pathlib import Path

from Muxer import Muxer

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
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite the original image file as output Live Photos",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose muxing")

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

    if args.input_directory is not None:
        input_directory = f"{Path(args.input_directory).resolve()}"
        # Going to search couples of file with ext (".heic", ".heif", ".avif", ".jpg", ".jpeg") (".mp4", ".mov")
        files = os.listdir(input_directory)
        videos = [
            f
            for f in files
            if os.path.isfile(os.path.join(input_directory, f))
            and Path(f).suffix.lower() in [".mp4", ".mov"]
        ]
        images = [
            f
            for f in files
            if os.path.isfile(os.path.join(input_directory, f))
            and Path(f).suffix.lower() in [".heic", ".heif", ".avif", ".jpg", ".jpeg"]
        ]

        for image in images:
            fname = Path(image).stem
            for ext in [".mp4", ".mov", ".MP4", ".MOV"]:
                if fname + ext in videos:
                    video = videos.pop(videos.index(fname + ext))

                    input_image = os.path.join(input_directory, image)
                    input_video = os.path.join(input_directory, video)

                    Muxer(
                        image_fpath=input_image,
                        video_fpath=input_video,
                        output_directory=args.output_directory,
                        delete_video=args.delete_video,
                        delete_temp=not args.keep_temp,
                        overwrite=args.overwrite,
                        verbose=args.verbose,
                    ).mux()
                    print("=" * 25)
                    break
    else:
        Muxer(
            image_fpath=args.input_image,
            video_fpath=args.input_video,
            output_fpath=args.output_file,
            output_directory=args.output_directory,
            delete_video=args.delete_video,
            delete_temp=not args.keep_temp,
            overwrite=args.overwrite,
            verbose=args.verbose,
        ).mux()