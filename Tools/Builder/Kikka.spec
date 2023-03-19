# -*- mode: python -*-
import os
import PyQt5
block_cipher = None

root_dir = os.path.abspath(os.curdir)
print(root_dir)

def list_all_files(path, exclude=()):
	for root, dirs, files in os.walk(path):
		# print root, dirs, files
		dirs[:] = [d for d in dirs if d not in exclude]
		for name in files:
			path = os.path.join(root, name)
			if path.endswith(".py"):
				mod = path.replace(path, "").replace(".py", "").replace(os.path.sep, ".")
				if mod.endswith("__init__"):
					mod = mod.replace(".__init__", "")
				yield mod

core_scripts = []
for i in list_all_files(os.path.join(root_dir, "Scripts")):
	i = i[1:]  # delete the first dot
	if i != '':
		core_scripts.append(i)

hidden_imports = [
	"os", "PyQt5.QtChart",
	"PyQt5.QtPrintSupport", "PyQt5.QtMultimedia", "PyQt5.QtMultimediaWidgets",
	"psutil", "win32api", "win32gui", "win32con", "win32process", "requests", 
]

hidden_imports.extend(core_scripts)
print("hidden_imports", hidden_imports)

datas = [
	(os.path.join(root_dir, "Resources", "Image"), os.path.join(".", "Resources", "Image")),
]

pyqt_dir = os.path.dirname(PyQt5.__file__)
pathex = [
	pyqt_dir,
	os.path.join(pyqt_dir, "Qt", "bin"),
	os.path.join(root_dir, "Scripts"),
	os.path.join(root_dir, "Ghosts"),
]

a = Analysis(
	[os.path.join(root_dir, "Main.py")],
    pathex=pathex,
    binaries=None,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=None,
    runtime_hooks=None,
    excludes=None,
    cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
	pyz,
	a.scripts,
	name='Kikka',
	version='temp/version_info.txt',
	icon=os.path.join(root_dir, "Resources", "Image", "icon.ico"),
	exclude_binaries=True,
	strip=False,
	upx=True,
	uac_admin=False, 
	debug=False,
	console=False
	)
	
coll = COLLECT(
	exe,
	a.binaries,
	a.zipfiles,
	a.datas,
	strip=False,
	upx=True,
	name='Kikka')