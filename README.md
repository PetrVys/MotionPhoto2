## Installation

Please make sure to have [ExifTool](https://exiftool.org/) installed on your computer.

Install dependeces `pip install -r requirements.txt`

## Usage

### Individual photos

To convert image and video pair to Motion Photo v2, run:

```
> python main.py --input-image ImageFile.HEIC --input-video VideoFile.MP4
```

### Directory mode
The script will automatically search file in directory that have the same name but different extension, for example: IMG_1496.HEIC, IMG_1496.MP4
```
> python main.py --input-directory /your/directory
```

### Notes
- The output of new images file will be: original_name.**LIVE**.ext
- If you provide a `--output-directory` the file will be: **output-directory**/original_name.ext
- While the script mux the images and video two temps files will be created and deleted automatically, you can keep it with `--keep-temp`
- If you want to remplace the original image file with the live one use: `--overwrite` (use at your risk)
- If you want to remove the video file after muxing use: `--delete-video` (use at your risk)

#### Documentation
- https://developer.android.com/media/platform/motion-photo-format
- https://medium.com/android-news/working-with-motion-photos-da0aa49b50c
