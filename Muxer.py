import logging
import exiftool
import os
import sys
import shutil

from pathlib import Path
from lxml import etree

from utils import (
    extract_track_number,
    extract_track_duration,
    read_file,
    enrich_fname,
)

import constants as const
from SamsungTags import SamsungTags

logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

class Muxer:
    def __init__(
        self,
        image_fpath: str,
        video_fpath: str,
        exiftool: exiftool.ExifToolHelper,
        output_fpath: str = None,
        output_directory: str = None,
        delete_video: bool = False,
        delete_temp: bool = True,
        overwrite: bool = False,
        no_xmp: bool = False,
        verbose: bool = False,
    ):
        self.logger = logging.getLogger(Path(image_fpath).stem)
        self.verbose = verbose
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        self.image_fpath = f"{Path(image_fpath).resolve()}"
        self.logger.debug("Image: %s", self.image_fpath)
        self.video_fpath = f"{Path(video_fpath).resolve()}"
        self.logger.debug("Video: %s", self.video_fpath)

        self.output_directory = output_directory
        self.overwrite = overwrite
        self.delete_video = delete_video
        self.no_xmp = no_xmp
        self.exiftool = exiftool

        if os.path.isfile(self.image_fpath) is False:
            self.logger.error("Image file doesn't exist")
            sys.exit(1)

        if os.path.isfile(self.video_fpath) is False:
            self.logger.error("Video file doesn't exist")
            sys.exit(1)

        if self.output_directory is not None:
            self.output_directory = f"{Path(output_directory).resolve()}"

            if os.path.exists(self.output_directory) is False:
                self.logger.error("Output directory doesn't exist, please create")
                sys.exit(1)

        if self.overwrite is True and output_fpath is not None:
            self.logger.error("Output file cannot be use overwrite option")
            sys.exit(1)

        if output_fpath is not None and self.output_directory is not None:
            self.logger.error("Output file cannot be use with output directory")
            sys.exit(1)

        if self.overwrite is True or self.delete_video is True:
            self.logger.warning(
                "Make sure to have a backup of your image and/or video file"
            )

        self.output_fpath = (
            os.path.join(self.output_directory, os.path.basename(self.image_fpath))
            if self.output_directory is not None
            else (
                self.image_fpath
                if overwrite is True
                else (
                    enrich_fname(self.image_fpath, "LIVE")
                    if output_fpath is None
                    else f"{Path(output_fpath).resolve()}"
                )
            )
        )
        
        self.org_outfpath = self.output_fpath

        self.delete_temp = delete_temp
        self.xmp = etree.fromstring(const.XMP)

    def change_xmpresource(self, value: str, attribute: str = const.ITEM_MIME, semantic: str = "Primary"):
        directory = self.xmp.find(".//Container:Directory", const.NAMESPACES)
        seq = directory.find("rdf:Seq", const.NAMESPACES)
        records = seq.findall(".//rdf:li[@rdf:parseType='Resource']", const.NAMESPACES)
        for record in records:
            item = record.find("Container:Item", const.NAMESPACES)
            semantic_attrib = item.attrib[const.ITEM_SEMANTIC]
            if semantic_attrib == semantic:
                item.set(attribute, value)

    def __validate_extension(self, fpath, metadata: dict = None) -> str:
        extension = Path(fpath).suffix
        if metadata is not None:
            metadata_extension = metadata.get("File:FileTypeExtension", None)
            if metadata_extension is not None:
                if extension[1:].lower() != metadata_extension.lower():
                    self.logger.warning(
                        "File extension %s doesn't match with metadata. Treating as %s",
                        extension,
                        metadata_extension,
                    )
                    extension = "." + metadata_extension
        return extension

    def validate_image(self, fpath: str, metadata: dict = None) -> str:
        # mime, encoding = mimetypes.guess_type(fpath)
        # fname = os.path.basename(fpath).lower()
        extension = self.__validate_extension(fpath, metadata=metadata)

        if extension.lower() in [".heic", ".heif", ".avif"]:
            image_type = "heic"  # Default is already with mimetype image/heic
        else:
            if extension.lower() not in [".jpg", ".jpeg"]:
                self.logger.warning(
                    "Image extension %s not supported. Treating as JPG", extension
                )
            image_type = "jpg"
            self.change_xmpresource("image/jpeg", semantic="Primary")
        return image_type

    def validate_video(self, fpath: str, metadata: dict = None) -> str:
        # mime, encoding = mimetypes.guess_type(fpath)
        # fname = os.path.basename(fpath).lower()
        extension = self.__validate_extension(fpath, metadata=metadata)

        if extension.lower() == ".mp4":
            video_type = "mp4"
            self.change_xmpresource("video/mp4", semantic="MotionPhoto")
        else:
            if extension.lower() != ".mov":
                self.logger.warning(
                    "Video extension %s not supported. Treating as QuickTime MOV",
                    extension,
                )
            video_type = "qt"  # Default is already with mimetype video/quicktime
        return video_type

    def fix_output_fpath(self, metadata: dict = None):
        output_path = Path(self.output_fpath)
        image_metadata_extension = (metadata or {}).get("File:FileTypeExtension", None)
        if image_metadata_extension is not None:
            if output_path.suffix[1:].lower() != image_metadata_extension.lower():
                self.logger.warning(
                    "Output extension %s doesn't match with input image metadata %s",
                    output_path.suffix,
                    image_metadata_extension,
                )

                self.output_fpath = os.path.join(
                    output_path.parent,
                    output_path.stem + f".{image_metadata_extension.lower()}",
                )

    def merge_xmp(self, xmp: str):
        try:
            xmp = etree.fromstring(xmp)
            xmp_description = xmp.find(".//rdf:Description", const.NAMESPACES)
            for child in xmp_description:
                # Just in case there are already MotionPhoto data, do not duplicate the Directory attribute
                if child.tag != const.CONTAINER_DIRECTORY:
                    self.logger.info("XMP metadata - copying %s", child)
                    self.xmp.find(".//rdf:Description", const.NAMESPACES).append(child)
            for attr in xmp_description.attrib:
                self.logger.info("XMP metadata - copying attribute %s", attr)
                self.xmp.find(".//rdf:Description", const.NAMESPACES).attrib[attr] = xmp_description.attrib.get(attr)
        except:
            self.logger.info("Could not copy (some of?) the XMP metadata tags from source.")

    def mux(self):
        self.logger.info("Processing %s", self.image_fpath)

        image_metadata, video_metadata = self.exiftool.get_metadata(
            [self.image_fpath, self.video_fpath]
        )
        
        for ns in const.NAMESPACES:
            etree.register_namespace(ns, const.NAMESPACES[ns])

        image_type = self.validate_image(self.image_fpath, metadata=image_metadata)
        self.fix_output_fpath(image_metadata)
        self.validate_video(self.video_fpath, metadata=video_metadata)

        if self.no_xmp is False:
            result = self.exiftool.execute(
                *[
                    "-X",
                    "-ee",
                    "-n",
                    "-QuickTime:StillImageTime",
                    "-QuickTime:TrackDuration",
                    f"{self.video_fpath}",
                ]
            )
            
            try:
                track_number = extract_track_number(result)
                self.logger.info("Live Photo keyframe track number: %s", track_number)

                track_duration = extract_track_duration(track_number, result)
                self.logger.info("Live Photo keyframe: %sus", track_duration)
                
                self.xmp.find(".//rdf:Description", const.NAMESPACES).set(
                    const.GCAMER_TIMESTAMP_US,
                    str(track_duration),
                )
            except:
                track_duration = -1
                self.logger.info("Could not read Live Photo keyframe (source video is probably not from Live Photo). No keyframe will be set.")

            video_data = read_file(self.video_fpath)
            samsung_tail = SamsungTags(video_data, image_type)
            
            result = self.exiftool.execute(*["-XMP", "-b", f"{self.image_fpath}"])
            if result == "":
                self.logger.warning("XMP of original file is empty")
            else:
                self.merge_xmp(result)
                
            self.change_xmpresource(str(samsung_tail.get_video_size()), attribute=const.ITEM_LENGTH, semantic="MotionPhoto")
            self.change_xmpresource(str(samsung_tail.get_image_padding()), attribute=const.ITEM_PADDING, semantic="Primary")

            xmp_updated = self.output_fpath + ".XMP"
            with open(xmp_updated, "wb" , encoding="utf-8") as f:
                f.write(etree.tostring(self.xmp, pretty_print=True))

            xmp_image = enrich_fname(self.output_fpath, "XMP")
            shutil.copyfile(self.image_fpath, xmp_image)
            self.exiftool.execute(
                *[
                    "-overwrite_original",
                    "-tagsfromfile",
                    xmp_updated,
                    "-xmp",
                    xmp_image,
                ]
            )
            
            merged_bytes = read_file(xmp_image)
        else:
            video_data = read_file(self.video_fpath)
            samsung_tail = SamsungTags(video_data, image_type)
            merged_bytes = read_file(self.image_fpath)
        samsung_tail.set_image_size(len(merged_bytes))
        video_footer = samsung_tail.video_footer()
        merged_bytes += video_footer

        self.logger.info("Writing output file: %s", self.output_fpath)
        with open(self.output_fpath, "wb") as binary_file:
            binary_file.write(merged_bytes)
        shutil.copystat(self.image_fpath, self.output_fpath)

        if self.delete_temp is True:
            os.remove(xmp_updated)
            self.logger.debug("Delete: %s", xmp_updated)
            os.remove(xmp_image)
            self.logger.debug("Delete: %s", xmp_image)

        if self.delete_video is True:
            os.remove(self.video_fpath)
            self.logger.debug("Delete: %s", self.video_fpath)
            
        if self.overwrite is True and self.output_fpath != self.org_outfpath:
            os.remove(self.org_outfpath)
            self.logger.debug("Delete: %s", self.org_outfpath)
