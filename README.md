# MotionPhoto2

A small script to create Motion Photo v2 from HEIC or JPG files and videos. Resulting files were tested with Google Photos and are accepted as motion/live photo; and when saved to iPhone from Google Photos, they turn back into Live Photos :-)

In case the source is an iPhone Live Photo, the presentation timestamp will be migrated as well, thus the photo will start from the same keyframe.

## Installation

In order to use this, please install [ExifTool](https://exiftool.org/) and put the files in the same directory as exiftool.exe. Alternatively, put location of exiftool.exe into system PATH variable.

## Usage

### Individual photos

To convert image and video pair to Motion Photo v2, run:

```
> MotionPhoto2.cmd ImageFile.HEIC VideoFile.MOV MotionPhoto.HEIC
```

Alternatively, you can run the powershell script directly:
```
PS> MotionPhoto2.ps1 -imageFile ImageFile.HEIC -videoFile VideoFile.MOV -outputFile MotionPhoto.HEIC
```

### Directory mode

To copy whole directory of photos, converting Live Photos to Motion Photos on the fly, create target directory and use the batch file in mode `MotionPhoto2.cmd SourceDir TargetDir`:

```
> CD \Photo Library
C:\Photo Library> MD "Fixed Library"
C:\Photo Library> MotionPhoto2.cmd . "Fixed Library"
```

## Limitations

If the source image is an Apple HDR HEIC image, Google Photos will say that the resulting photo is not HDR. This is not true - if you save the photo back to iPhone camera roll, you'll see the photo is HDR.

Google Photos _will_ actually show it too, but only when it is stored in local photos on an iPhone/iPad.

The reason is probably directly related to Motion Photos -  the same place where Motion Photos are defined (in XMP object GCamera - `http://ns.google.com/photos/1.0/camera/`) is also the place where Google/Android stores JPEG/R HDR information.

It appears that the server-side processing of Google Photos does not check for Apple HDR once it finds Google Camera header in XMP tags. The two formats appear to be significantly different, thus an easy conversion is not possible. See [Issue #2](https://github.com/PetrVys/MotionPhoto2/issues/2) for more details.

Hopefully, as Gainmap HDR matures, both Google and Apple will converge on ISO/CD 21496-1 and things will just start working. On Apple side this has happened already - as of iOS18 RC on iPhone 15(pro), iOS stores HDR in ISO "tmap" format. Unfortunately iPhones 12-14 are stuck with Apple Gainmaps. On Google side keep an eye on [libultrahdr](https://github.com/google/libultrahdr) used in Android and also most likely in GPhotos backend. It currently only supports JPEG/R, but HEIC support [is on the way](https://github.com/google/libultrahdr/issues/195).

## About

The script is written with Windows in mind, but it should be possible to use it on Linux and MacOS PowerShell too (possibly with some tweaking of the used .Net objects). Patches for this are welcome.

Photos are created to mimic the way Galaxy S20 FE phones create HEIC motion photos. This format internally refers to itself as mpv2, which is referred to in this document as Motion Photo version 2 (even though the XMP tag still says it's version 1).
Thanks to [@tribut](https://github.com/tribut) for uploading a sample photo [here](https://github.com/photoprism/photoprism/issues/1739#issuecomment-1216457652). Without it, this project would never start, as this format is very different from original Motion Photo spec and seems to be amalgamation of Google and Samsung ideas on how to store image and video in the same file.
