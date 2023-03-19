
set ghost_path=%1
if "%ghost_path%"=="" set /p ghost_path=ghost path:

py -3 ghost_pack.py -p %ghost_path% -o . -z

pause
