set shell_path=%1
if "%shell_path%"=="" set /p shell_path=shell path:

py -3 FormatShellImage.py %shell_path%

pause
