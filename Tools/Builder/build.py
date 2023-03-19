import os
import sys
import zipfile
import argparse
import shutil
import subprocess
import configparser

VERSION = "0.9.0"
RELEASE_TYPE = "Debug"
PROGRAM_NAME = "Kikka"

BUILDER_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(BUILDER_PATH, "..", ".."))
BUILD_DIR = os.path.join(BUILDER_PATH, "build")
WORK_DIR = os.path.join(BUILDER_PATH, "temp")

SPEC_FILE = os.path.join(BUILDER_PATH, "Kikka.spec")
VERSION_INFO_FILE = os.path.join(WORK_DIR, "version_info.txt")

COMPANY = "Kikka SSP"
DESCRIPTION = "Kikka SSP"
INTERNAL = "Kikka"
COPYRIGHT = "Copyright 2019-2020"
ORIGINAL = "Kikka.exe"
PRODUCT = "Kikka"
LANGUAGE = "zh"


def clear():
    print("\n==== clear build ====================")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)
    os.makedirs(BUILD_DIR)
    os.makedirs(WORK_DIR)

    print("done")


def update_file_version_info(output, version, company, description, internal, copyright, original, product, language):
    os.chdir(BUILDER_PATH)
    template = r"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=%FILE_VERS%,
    prodvers=%PROD_VERS%,
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u'%COMPANY%"'),
        StringStruct(u'FileDescription', u'%DESCRIPTION%'),
        StringStruct(u'FileVersion', u'%FILE_VERSION%'),
        StringStruct(u'InternalName', u'%INTERNAL%'),
        StringStruct(u'LegalCopyright', u'%COPYRIGHT%'),
        StringStruct(u'OriginalFilename', u'%ORIGINAL%'),
        StringStruct(u'ProductName', u'%PRODUCT%'),
        StringStruct(u'ProductVersion', u'%PRODUCT_VERSION%'),
        StringStruct(u'LanguageId', u'%LANGUAGE%')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"""

    if '-' in version:
        version = version[:version.find('-')]
    if '+' in version:
        version = version[:version.find('+')]

    ver = version.split('.')
    for i in range(len(ver), 4):
        ver.append('0')

    file_vers = "(%s, %s, %s, %s)" % (ver[0], ver[1], ver[2], ver[3])
    prod_vers = "(%s, %s, %s, %s)" % (ver[0], ver[1], ver[2], ver[3])
    file_version = "%s.%s.%s.%s" % (ver[0], ver[1], ver[2], ver[3])
    product_version = "%s.%s.%s.%s" % (ver[0], ver[1], ver[2], ver[3])

    text = template
    text = text.replace(r"%FILE_VERS%", file_vers)
    text = text.replace(r"%PROD_VERS%", prod_vers)
    text = text.replace(r"%FILE_VERSION%", file_version)
    text = text.replace(r"%PRODUCT_VERSION%", product_version)
    text = text.replace(r"%COMPANY%", company)
    text = text.replace(r"%DESCRIPTION%", description)
    text = text.replace(r"%INTERNAL%", internal)
    text = text.replace(r"%COPYRIGHT%", copyright)
    text = text.replace(r"%ORIGINAL%", original)
    text = text.replace(r"%PRODUCT%", product)
    text = text.replace(r"%LANGUAGE%", language)

    dir = os.path.dirname(output)
    if not os.path.exists(dir):
        os.makedirs(dir)

    dst = open(output, "w", encoding='utf-8')
    dst.write(text)
    dst.close()


def check_virtual_environment():
    print("\n==== check virtual environment ====================")

    pip_file = os.path.join(ROOT_PATH, "Pipfile")
    pip_lock = os.path.join(ROOT_PATH, "Pipfile.lock")
    if not os.path.isfile(pip_file) or not os.path.isfile(pip_lock):
        return False

    config = configparser.ConfigParser()
    config.read(pip_file)

    flag = True
    try:
        if config.get("packages","pyinstaller") != '"*"':
            return False
        if config.get("packages","pyqt5") != '"!=5.13.0"':
            return False
        if config.get("packages","requests") != '"*"':
            return False
        if config.get("packages","pywin32") != '"*"':
            return False
        if config.get("packages","psutil") != '"*"':
            return False
        if config.get("packages","six") != '"*"':
            return False
        if config.get("requires","python_version") != '"3.6"':
            return False
    except Exception:
        return False

    subprocess.call("py -m pipenv run pip list")
    print("done")
    return flag


def make_virtual_environment():

    if check_virtual_environment():
        return

    print("\n==== make virtual environment ====================")

    os.chdir(ROOT_PATH)
    subprocess.call("py -m pipenv --python 3.6.8")

    subprocess.call("py -m pipenv install pyinstaller")
    subprocess.call("py -m pipenv install pyqt5!=5.13.0")
    subprocess.call("py -m pipenv install requests")
    subprocess.call("py -m pipenv install pywin32")
    subprocess.call("py -m pipenv install psutil")
    subprocess.call("py -m pipenv install six")

    subprocess.call("py -m pipenv run pip list")
    print("done")


def build(is_debug=False):
    print("\n==== build ====================")

    os.chdir(ROOT_PATH)
    ret = subprocess.call(
        "py -m pipenv run PyInstaller %s --noconsole --name %s --distpath %s --workpath %s --version-file=%s"
        % (SPEC_FILE, PROGRAM_NAME, BUILD_DIR, WORK_DIR, VERSION_INFO_FILE)
    )
    if ret == 0:
        print("done")
        return True
    else:
        print("error code:", ret)
        return False


def pack_ghost():
    print("\n==== pack ghost ====================")
    ghost_pack = os.path.join(ROOT_PATH, "Tools", "GhostPack", "ghost_pack.py")
    ghost_dir = os.path.join(ROOT_PATH, "Ghosts")
    ghost_output = os.path.join(BUILD_DIR, PROGRAM_NAME, "Ghosts")
    os.makedirs(ghost_output)

    ghosts = os.listdir(ghost_dir)
    for ghost in ghosts:
        ghost_path = os.path.join(ghost_dir, ghost)
        if not os.path.isdir(ghost_path):
            continue

        ret = subprocess.call(
            "py -3 %s -p %s -o %s" % (ghost_pack, ghost_path, ghost_output)
        )
        if ret == 0:
            print("done")
            return True
        else:
            print("error code:", ret)
            return False

def copy_file():
    # shutil.copytree(os.path.join(ROOT_PATH, "Resources"), os.path.join(BUILD_DIR, PROGRAM_NAME, "Resources"))
    pass

def run():
    os.system("cls")
    clear()

    update_file_version_info(VERSION_INFO_FILE, VERSION, COMPANY, DESCRIPTION, INTERNAL, COPYRIGHT, ORIGINAL, PRODUCT, LANGUAGE)

    make_virtual_environment()

    if not build():
        print("FAIL")
        sys.exit(-1)

    pack_ghost()
    copy_file()

    print("\nSUCCEED")


if __name__ == '__main__':
    run()

