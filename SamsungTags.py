import os
import sys
import struct

import constants as const

class SamsungTags:
    
    # This class is responsible for creating the video footer that is attached after image data
    # It also creates offsets for the XMP image/video in the main image. 
    
    def __init__(
        self,
        video_bytes: bytes,
        image_type: str = "heic"
    ):
        self.video_bytes = video_bytes
        self.video_size = len(video_bytes)
        self.image_type = image_type
        self.image_size = 0 # we don't know yet - image size may change after we fill in the XMP tags about video
        self.tags = {"MotionPhoto_Version": bytes("mpv3", "utf-8")}
        if self.image_type not in ["heic"]:
            self.tags["MotionPhoto_Data"] = self.video_bytes
        else:
            self.tags["MotionPhoto_Data"] = bytes("mpv2___.___.", "utf-8") # dummy data for length computation

    def set_image_size(self, image_size: int):
        self.image_size = image_size
        if self.image_type in ["heic"]:
            video_offset = self.image_size + const.MPVD_BOX_SIZE
            mp_data = bytes("mpv2", "utf-8")
            mp_data += struct.pack(">i", video_offset)
            mp_data += struct.pack(">i", self.video_size)
            self.tags["MotionPhoto_Data"] = mp_data
        
    def get_image_padding(self) -> int:
        if self.image_type in ["heic"]:
            return const.MPVD_BOX_SIZE
        size = 0
        for tag in const.SAMSUNG_TAG_IDS:
            if tag in self.tags:
                size += len(const.SAMSUNG_TAG_IDS[tag])
                size += 4 # place to put size of string on next line
                size += len(tag)
                if tag == "MotionPhoto_Data": return size
                size += len(self.tags[tag])
        return -1 # should never come here
    
    def get_video_size(self) -> int:
        return len(self.video_footer()) - self.get_image_padding()

    def video_footer(self) -> bytes:
        tag_data = b''
        tag_offsets = {}
        tag_lengths = {}
        for tag in const.SAMSUNG_TAG_IDS:
            if tag in self.tags:
                tag_bytes =  const.SAMSUNG_TAG_IDS[tag]
                tag_bytes += struct.pack("<i", len(tag))
                tag_bytes += bytes(tag, "utf-8")
                tag_bytes += self.tags[tag]
                tag_data += tag_bytes
                tag_length = len(tag_bytes)
                tag_lengths[tag] = tag_length
                for preceding_tag in const.SAMSUNG_TAG_IDS:
                    if preceding_tag in self.tags:
                        tag_offsets[preceding_tag] = tag_length + (tag_offsets[preceding_tag] if preceding_tag in tag_offsets else 0)
                        if preceding_tag == tag:
                            break

        sefh = b''
        sefh += bytes("SEFH", "utf-8")
        sefh += struct.pack("<i", const.SAMSUNG_SEFH_VERSION)
        sefh += struct.pack("<i", len(self.tags))
        for tag in const.SAMSUNG_TAG_IDS:
            if tag in self.tags:
                sefh += const.SAMSUNG_TAG_IDS[tag]
                sefh += struct.pack("<i", tag_offsets[tag])
                sefh += struct.pack("<i", tag_lengths[tag])
        sefh_len = len(sefh)
        sefh += struct.pack("<i", sefh_len)
        sefh += bytes("SEFT", "utf-8")
        
        result = b''
        if self.image_type in ["heic"]:
            result += self.video_bytes
            result += struct.pack(">i", len(tag_data) + len(sefh) + const.SEFD_BOX_SIZE)
            result += const.SEFD_BOX_NAME
        result += tag_data
        result += sefh
        if self.image_type in ["heic"]:
            mpvd_header = struct.pack(">i", len(result) + const.MPVD_BOX_SIZE)
            mpvd_header += const.MPVD_BOX_NAME
            result = mpvd_header + result
            
        return result