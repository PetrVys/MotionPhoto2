param (
    [Parameter(Mandatory)] [String] $imageFile
  , [Parameter(Mandatory)] [String] $videoFile
  , [Parameter(Mandatory)] [String] $outputFile
)

function runCmdAndCaptureOutput(
    [Parameter(Mandatory=$true)]
    [string] $cmd
) {
    [string] $errOut
    [string] $stdOut
    Invoke-Expression $cmd -ErrorVariable errOut -OutVariable stdOut | Out-Null
    if($LASTEXITCODE -ne 0) {
        Write-Host -ForegroundColor Red "LASTEXITCODE: $LASTEXITCODE"
        throw $LASTEXITCODE
    } 
    return $stdOut
}

function readFile(
    [Parameter(Mandatory=$true)]
    [string] $file
) {
    [System.IO.File]::ReadAllBytes($file)
}

function getStillImageTime(
    [Parameter(Mandatory=$true)]
    [string] $mov,
    [Parameter(Mandatory=$true)]
    [string] $exiftool
) {
    [String[]]$out = runCmdAndCaptureOutput "& '$($exiftool)' -X -ee -n -QuickTime:StillImageTime -QuickTime:TrackDuration ""$($mov)"""
    [String] $presentationTimestampText = "#NaN"
    [Int] $presentationTimestamp = 0
    [String] $trackNumber = "Missing"

    $out | select-string -allmatches -pattern '^\s*<Track(\d+):StillImageTime>-1<' | % { $trackNumber = $_.Matches.Groups[1].Value }
    if ($trackNumber -ne "Missing") {
        $out | select-string -allmatches -pattern "^\s*<Track$($trackNumber):TrackDuration>(\d+\.?\d*)<" | % { $presentationTimestampText = $_.Matches.Groups[1].Value }
    }
    try { 
      $d = [double] $presentationTimestampText 
      $presentationTimestamp = [Math]::Round($d * 1000000)
    } catch { 
      $presentationTimestamp = -1
    }
    $presentationTimestamp
}

function validateImage(
    [Parameter(Mandatory=$true)]
    [string] $imageFile,
    [Parameter(Mandatory=$true)]
    [XML] $xmp
) {
    switch (([io.fileinfo]$imageFile).Extension.ToLower()) {
        ".jpg" { $imageType = "jpg"; $xmp.xmpmeta.RDF.Description.Directory.Seq.li[0].Item.Mime = 'image/jpeg' }
        ".jpeg" { $imageType = "jpg"; $xmp.xmpmeta.RDF.Description.Directory.Seq.li[0].Item.Mime = 'image/jpeg' }
        ".heic" { $imageType = "heic" }
        ".heif" { $imageType = "heic" }
        ".avif" { $imageType = "heic" }
        default {
            # If the input file is of some HEIC variety with unknow extension, then the omission of mpvd box will cause it to not be accepted by GPhotos (upload will fail)
            # But if we add mpvd box to jpg-style image, it'll also not be accepted
            Write-Output "WARNING - image extension $(([io.fileinfo]$imageFile).Extension) not supported. Treating as JPG"
            $imageType = "jpg"
            $xmp.xmpmeta.RDF.Description.Directory.Seq.li[0].Item.Mime = 'image/jpeg'
        }
    }

    if (([io.fileinfo]$imageFile).Extension.ToLower() -ne ([io.fileinfo]$outputFile).Extension.ToLower()) {
        Write-Output "Warning - different extension between source and target file!"
    }

    if (-Not (Test-Path $imageFile -PathType Leaf)) {
        Write-Error "ERROR: source image file $($imageFile) does not exist!"
        exit 1
    }
    
    $imageType
}

function validateVideo(
    [Parameter(Mandatory=$true)]
    [string] $videoFile,
    [Parameter(Mandatory=$true)]
    [XML] $xmp
) {
    switch (([io.fileinfo]$videoFile).Extension.ToLower()) {
        ".mov" { $videoType = "qt" }
        ".mp4" { $videoType = "mp4"; $xmp.xmpmeta.RDF.Description.Directory.Seq.li[1].Item.Mime = 'video/mp4' }
        default {
            # This is genuinely just warning - just add correct mime type above and it should just work
            Write-Output "WARNING - video extension $(([io.fileinfo]$videoFile).Extension) not supported. Treating as QuickTime MOV"
            $videoType = "qt"
        }
    }

    if (-Not (Test-Path $videoFile -PathType Leaf)) {
        Write-Error "ERROR: source video file $($videoFile) does not exist!"
        exit 2
    }

    $videoType
}
# The movie's Item:Length is in bytes from the end of the file and points to [mpv2][offset][size] structure
# The image's Item:Padding is a mystery - in the golden source file it was 67 when movie's length was 68, so it is set to one less again
#     According to v1 specs, it probably should be 8 or 0 (the size of mpvd box), but whatever... This file does not look like v1 type...
# In any case, these two numbers appear to be ignored by Google Photos (they split the video data based on samsung trailer structure values)
[XML]$xmp = @'
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
'@
                                               # Before the box name goes it's size
[byte[]] $mpvdBoxName = 0x6D, 0x70, 0x76, 0x64 # "mpvd"

[byte[]] $samsungTailStart = 0x00, 0x00, 0x00, 0x4c, # Length of the SamsungTrailer block
                             0x73, 0x65, 0x66, 0x64, # Samsung trailer header / HEIC top-level box ("sefd")
                             0x00, 0x00, 0x30, 0x0a, # Motion Photo Data tag header
                             0x10, 0x00, 0x00, 0x00, # 16 - length of string on next line
                             0x4d, 0x6f, 0x74, 0x69, 0x6f, 0x6e, 0x50, 0x68, 0x6f, 0x74, 0x6f, 0x5f, 0x44, 0x61, 0x74, 0x61, # Human-readable tag name "MotionPhoto_Data"
                             0x6d, 0x70, 0x76, 0x32  # "mpv2" - I guess "Motion Photo version 2"?
                             # Between $samsungTailStart and $samsungTailEnd go two Big-Endian encoded Int32 - video start offset from the start of the file and video length
[byte[]] $samsungTailEnd = 0x53, 0x45, 0x46, 0x48,   # "SEFH" - lists all Samsung Trailer tags (as there are no pointers/sizes/structures above)
                           0x6b, 0x00, 0x00, 0x00,   # Version 107 (encoded in little endian!)
                           0x01, 0x00, 0x00, 0x00,   # Number of tags contained in the trailer (little-endian)
                           0x00, 0x00, 0x30, 0x0a,    # Motion Photo Data tag header (again!)
                           0x24, 0x00, 0x00, 0x00,    # Negative offset from start of the $samsungTailEnd into $samsungTailStart (including video offsets)
                           0x24, 0x00, 0x00, 0x00,    # Length of the tag
                           0x18, 0x00, 0x00, 0x00,   # Length of the SEFH structure until previous line
                           0x53, 0x45, 0x46, 0x54    # "SEFT" - Samsung trailer end

Write-Output "Motion Photo v2 muxer (heic compatible). Free your Live Photos!"
Write-Output "(C) 2024 Petr Vyskocil. Licensed under MIT license."
Write-Output ""

$imageFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($imageFile)
$videoFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($videoFile)
$outputFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($outputFile)

# Basic validation + setting of mime type within XMP
$imageType = validateImage $imageFile $xmp
$videoType = validateVideo $videoFile $xmp

if (Test-Path ("$($PSScriptRoot)\exiftool.exe") -PathType Leaf) {
    $exifTool="$($PSScriptRoot)\exiftool.exe" # take exiftool from script's directory
} else {
    $exifTool='exiftool.exe'                # try to run exiftool from path
}

Write-Output "Trying to extract LivePhoto timestamp..."
[Int] $presentationTimestamp = getStillImageTime $videoFile $exifTool

if ($presentationTimestamp -ne -1) {
    Write-Output "Extracted LivePhoto timestamp $($presentationTimestamp)us from QuickTime."
} else {
    Write-Output "Failed, timestamp will not be set in resulting MotionPhoto."
}

$xmp.xmpmeta.RDF.Description.MotionPhotoPresentationTimestampUs = [String]$presentationTimestamp

Write-Output "Writing MotionPhoto metadata to the image..."

Remove-Item -ErrorAction Ignore "$($outputFile).tmp1" 
Copy-Item $imageFile -Destination "$($outputFile).tmp1"
Remove-Item -ErrorAction Ignore "$($outputFile).tmp2" 

# Copy attributes from existing XMP file
$existingXmpString = runCmdAndCaptureOutput "& '$($exifTool)' -XMP -b ""$($outputFile).tmp1""" 
try { 
    $existingXmp = [XML] $existingXmpString
    ForEach ($XmlNode in $existingXmp.xmpmeta.RDF.Description.ChildNodes) {
        if ($XmlNode.Name -NotMatch 'Directory$') { # Just in case there are already MotionPhoto data, do not duplicate the Directory attribute
            $xmp.xmpmeta.RDF.Description.AppendChild($xmp.ImportNode($XmlNode, $true)) | Out-Null
        }
    }
} catch { 
    # do nothing - most likely cast to XML has failed or attributes are missing; no tags will be copied
}

# save XMP file with added MotionPhoto attributes
$xmp.Save("$($outputFile).tmp2")

# Replace XMP attributes in the still image file with above new XMP
runCmdAndCaptureOutput "& '$($exifTool)' -overwrite_original -tagsfromfile ""$($outputFile).tmp2"" -xmp ""$($outputFile).tmp1""" | Out-Null

Write-Output "Stitching image and video together into MotionPhoto..."

[byte[]] $image = readFile -file "$($outputFile).tmp1"
[byte[]] $video = readFile -file $videoFile

[int] $imageSz = $image.Count
[int] $videoSz = $video.Count

if ($imageType -eq 'heic') {
    [int32] $mpvdSizeInt = $videoSz + 8 + 76 # 8 - mpvd box size, 76 - size of full footer ($samsungTailStart + $videoOffset + $videoSize + $samsungTailEnd)
    [int32] $videoOffsetInt = $imageSz + 8 # 8 is the size of mpvd box
} else {
    [int32] $mpvdSizeInt = 0
    [int32] $videoOffsetInt = $imageSz
}
[byte[]] $mpvdSize = [System.BitConverter]::GetBytes($mpvdSizeInt) 
[Array]::Reverse($mpvdSize) # these three are written in Big Endian, thus the [Array]::Reverse to flip bytes around
[byte[]] $videoOffset = [System.BitConverter]::GetBytes($videoOffsetInt) 
[Array]::Reverse($videoOffset)
[byte[]] $videoSize = [System.BitConverter]::GetBytes([int32]($videoSz ))
[Array]::Reverse($videoSize)

Remove-Item -ErrorAction Ignore "$($outputFile).tmp1"
Remove-Item -ErrorAction Ignore "$($outputFile).tmp2"
Remove-Item -ErrorAction Ignore $outputFile

$fs = [System.IO.File]::OpenWrite($outputFile)
$ws = [System.IO.BinaryWriter]::new($fs)
$ws.Write($image)
if ($imageType -eq 'heic') {
    $ws.Write($mpvdSize)
    $ws.Write($mpvdBoxName)
}
$ws.Write($video)
$ws.Write($samsungTailStart)
$ws.Write($videoOffset)
$ws.Write($videoSize)
$ws.Write($samsungTailEnd)
$ws.Flush()
$ws.Dispose()

(Get-Item $outputFile).LastWriteTime = (Get-Item $imageFile).LastWriteTime

Write-Output "Done."

