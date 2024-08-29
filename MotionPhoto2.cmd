@ECHO OFF
SETLOCAL EnableDelayedExpansion
SETLOCAL EnableExtensions

IF "%~1" == "" GOTO:Usage
IF EXIST "%~1\*" GOTO:ProcessDirectory

powershell.exe -executionpolicy bypass -nologo -file "%~dp0MotionPhoto2.ps1" -imageFile "%~1" -videoFile "%~2" -outputFile "%~3"
GOTO:EOF

:ProcessDirectory
SET _SOURCE=%~f1
SET _TARGET=%~f1
IF NOT "%~2" == "" (
	IF NOT EXIST "%~f2\*" (
		ECHO Target directory "%~f2" does not exist!
		EXIT /b 1
	)
	SET _TARGET=%~f2
)
ECHO Processing directory [%~f1] to directory [%_TARGET%]
ECHO.
CALL:strlen _SOURCE _SOURCE_LEN
CALL:strlen _TARGET _TARGET_LEN

FOR /R "%_SOURCE%" %%a IN (*.jpeg,*.jpg,*.heic,*.heif) DO (
	SET _SOURCEDIR=%%~dpa
	REM _TARGETCHK is substring of the file to process of the length of _TARGET. In case target is subdir of source, do not process the files aready in target.
	CALL SET "_TARGETCHK=!_SOURCEDIR:~0,%_TARGET_LEN%!"
	IF /I "!_TARGETCHK!" NEQ "%_TARGET%" (
		REM _TARGETDIR is set to _TARGET + relative path in _SOURCE (without filename)
		CALL SET "_TARGETDIR=%%_TARGET%%!_SOURCEDIR:~%_SOURCE_LEN%!"
		FOR %%b IN ("%%~dpna.mov","%%~dpna.mp4") DO (
			IF EXIST "%%~b" (
				IF NOT EXIST "!_TARGETDIR!\*" (
					ECHO Creating target subdirectory [!_TARGETDIR!]
					MD "!_TARGETDIR!" || EXIT /b 1
				)
				ECHO Converting [%%~a] and [%%~b] to [!_TARGETDIR!%%~nxa]
				powershell.exe -executionpolicy bypass -nologo -file "%~dp0MotionPhoto2.ps1" -imageFile "%%~a" -videoFile "%%~b" -outputFile "!_TARGETDIR!%%~nxa" || EXIT /b 1
				ECHO.
			)
		)
	)
)

REM And now, that all Live Photos have been converted to MotionPhotos, copy the rest of the files over too...
FOR /R "%_SOURCE%" %%a IN (*.*) DO (
	SET _SOURCEDIR=%%~dpa
	CALL SET "_TARGETCHK=!_SOURCEDIR:~0,%_TARGET_LEN%!"
	IF /I "!_TARGETCHK!" NEQ "%_TARGET%" (
		CALL SET "_TARGETDIR=%%_TARGET%%!_SOURCEDIR:~%_SOURCE_LEN%!"
		IF NOT EXIST "!_TARGETDIR!%%~nxa" (
			SET _VIDEO=false
			SET _SKIPCOPY=false
			IF /I [%%~xa] == [.mov] SET _VIDEO=true
			IF /I [%%~xa] == [.mp4] SET _VIDEO=true
			IF [!_VIDEO!] == [true] (
				FOR %%b IN ("%%~dpna.jpeg", "%%~dpna.jpg", "%%~dpna.heic", "%%~dpna.heif") DO IF EXIST "%%~b" SET _SKIPCOPY=true
			)
			IF [!_SKIPCOPY!] == [false] (
				IF NOT EXIST "!_TARGETDIR!\*" (
					ECHO Creating target subdirectory [!_TARGETDIR!]
					MD "!_TARGETDIR!" || exit /b 1
				)
				ECHO Copying regular file [%%~a] to [!_TARGETDIR!]
				COPY "%%~a" "!_TARGETDIR!%%~nxa" > nul || exit /b 1
			)
		)
	)
)
GOTO:EOF

:strlen  StrVar  [RtnVar]
  set "s=#!%~1!"
  set "len=0"
  for %%N in (4096 2048 1024 512 256 128 64 32 16 8 4 2 1) do (
    if "!s:~%%N,1!" neq "" (
      set /a "len+=%%N"
      set "s=!s:~%%N!"
    )
  )
  if "%~2" neq "" (set %~2=%len%) else echo %len%
GOTO:EOF

:Usage
ECHO Parameters missing.
ECHO.
ECHO To process a single file:
ECHO %~nx0 image_file.(jpg^|heic) video_file.(mov^|mp4) output_file.(jpg^|heic)
ECHO.
ECHO Example:
ECHO %~nx0 IMG_0001.heic IMG_001.mov ..\fixed\IMG_0001.heic
ECHO.
ECHO To process a directory:
ECHO %~nx0 input_directory [output_directory]
ECHO.
ECHO Example (note that output directory has to exist as a safety feature):
ECHO MD "Camera Roll\Fixed"
ECHO %~nx0 "Camere Roll" "Camera Roll\Fixed"
ECHO.
ECHO All files in input directory will be copied to output directory, except LivePhotos.
ECHO Those will be merged and saved as MotionPhoto in target.
ECHO Subdirectories are supported.
ECHO In case output directory is missing, files are modified in place.
ECHO This is not really recommended - you'll lose the original file and there
ECHO will also be a now-unneccessary movie files left around.
GOTO:EOF