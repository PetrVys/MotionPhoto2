@ECHO OFF
powershell.exe -executionpolicy bypass -nologo -file "%~dp0MotionPhoto2.ps1" -imageFile "%~1" -videoFile "%~2" -outputFile "%~3"