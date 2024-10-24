XMP = """
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.1.0-jc003">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:GCamera="http://ns.google.com/photos/1.0/camera/"
        xmlns:Container="http://ns.google.com/photos/1.0/container/"
        xmlns:Item="http://ns.google.com/photos/1.0/container/item/"
        xmlns:HDRGainMap="http://ns.apple.com/HDRGainMap/1.0/"
      GCamera:MotionPhoto="1"
      GCamera:MotionPhotoVersion="1"
      GCamera:MotionPhotoPresentationTimestampUs="-1">
      <Container:Directory>
        <rdf:Seq>
          <rdf:li rdf:parseType="Resource">
            <Container:Item
              Item:Mime="image/heic"
              Item:Semantic="Primary"
              Item:Length="0"
              Item:Padding="8"/>
          </rdf:li>
          <rdf:li rdf:parseType="Resource">
            <Container:Item
              Item:Mime="video/quicktime"
              Item:Semantic="MotionPhoto"
              Item:Length="404"
              Item:Padding="0"/>
          </rdf:li>
        </rdf:Seq>
      </Container:Directory>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
"""

NAMESPACES = {
    "x": "adobe:ns:meta/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "GCamera": "http://ns.google.com/photos/1.0/camera/",
    "Container": "http://ns.google.com/photos/1.0/container/",
    "Item": "http://ns.google.com/photos/1.0/container/item/",
    "HDRGainMap": "http://ns.apple.com/HDRGainMap/1.0/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "photoshop": "http://ns.adobe.com/photoshop/1.0/",
    "mwg-rs": "http://www.metadataworkinggroup.com/schemas/regions/",
    "stArea": "http://ns.adobe.com/xmp/sType/Area#",
    "apple-fi": "http://ns.apple.com/faceinfo/1.0/",
    "stDim": "http://ns.adobe.com/xap/1.0/sType/Dimensions#",
    "hdrgm": "http://ns.adobe.com/hdr-gain-map/1.0/",
    "xmpNote": "http://ns.adobe.com/xmp/note/"
}

CONTAINER_DIRECTORY = "{" + NAMESPACES["Container"] + "}Directory"
CONTAINER_SEMANTIC = "{" + NAMESPACES["Container"] + "item/}Semantic"
CONTAINER_MIME = "{" + NAMESPACES["Container"] + "item/}Mime"
CONTAINER_LENGTH = "{" + NAMESPACES["Container"] + "item/}Length"
CONTAINER_PADDING = "{" + NAMESPACES["Container"] + "item/}Padding"
GCAMER_TIMESTAMP_US = "{" + NAMESPACES["GCamera"] + "}MotionPhotoPresentationTimestampUs"

MPVD_BOX_SIZE = 8
MPVD_BOX_NAME = bytes("mpvd", "utf-8")

SEFD_BOX_SIZE = 8
SEFD_BOX_NAME = bytes("sefd", "utf-8")

SAMSUNG_TAG_IDS = {
    "Image_UTC_Data":           bytes([0x00, 0x00, 0x01, 0x0a]),
    "MCC_Data":                 bytes([0x00, 0x00, 0xa1, 0x0a]),
    "Camera_Scene_Info":        bytes([0x00, 0x00, 0x01, 0x0d]),
    "Color_Display_P3":         bytes([0x00, 0x00, 0xc1, 0x0c]),
    "Camera_Capture_Mode_Info": bytes([0x00, 0x00, 0x61, 0x0c]),
    "MotionPhoto_Data":         bytes([0x00, 0x00, 0x30, 0x0a]),
    "MotionPhoto_Version":      bytes([0x00, 0x00, 0x31, 0x0a])
}

SAMSUNG_SEFH_VERSION = 107