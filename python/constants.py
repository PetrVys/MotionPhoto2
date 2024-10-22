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
              Item:Padding="43"/>
          </rdf:li>
          <rdf:li rdf:parseType="Resource">
            <Container:Item
              Item:Mime="video/quicktime"
              Item:Semantic="MotionPhoto"
              Item:Length="44"
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
GCAMER_TIMESTAMP_US = "{" + NAMESPACES["GCamera"] + "}MotionPhotoPresentationTimestampUs"

MPVD_BOX_NAME = bytes([0x6D, 0x70, 0x76, 0x64])  # "mpvd"
SAMUSING_TAIL_START = bytes([
    0x00, 0x00, 0x00, 0x4c,  # Length of the SamsungTrailer block
    0x73, 0x65, 0x66, 0x64,  # Samsung trailer header / HEIC top-level box ("sefd")
    0x00, 0x00, 0x30, 0x0a,  # Motion Photo Data tag header
    0x10, 0x00, 0x00, 0x00,  # 16 - length of string on next line
    0x4d, 0x6f, 0x74, 0x69, 0x6f, 0x6e, 0x50, 0x68, 0x6f, 0x74, 0x6f, 0x5f, 0x44, 0x61, 0x74, 0x61,  # Human-readable tag name "MotionPhoto_Data"
    0x6d, 0x70, 0x76, 0x32   # "mpv2" - I guess "Motion Photo version 2"?
])
SAMUSING_TAIL_END = bytes([
    0x53, 0x45, 0x46, 0x48,   # "SEFH" - lists all Samsung Trailer tags (as there are no pointers/sizes/structures above)
    0x6b, 0x00, 0x00, 0x00,   # Version 107 (encoded in little endian!)
    0x01, 0x00, 0x00, 0x00,   # Number of tags contained in the trailer (little-endian)
    0x00, 0x00, 0x30, 0x0a,   # Motion Photo Data tag header (again!)
    0x24, 0x00, 0x00, 0x00,   # Negative offset from start of the $samsungTailEnd into $samsungTailStart (including video offsets)
    0x24, 0x00, 0x00, 0x00,   # Length of the tag
    0x18, 0x00, 0x00, 0x00,   # Length of the SEFH structure until previous line
    0x53, 0x45, 0x46, 0x54    # "SEFT" - Samsung trailer end
])