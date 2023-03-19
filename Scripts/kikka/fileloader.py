
import os
import logging
import zipfile

from PyQt5.QtGui import QImage

import kikka


class FileLoader:
    def __init__(self, root_path):
        self.root_path = root_path
        self.is_zip = False
        self.is_initialized = False

        self.namelist = []
        self.image_list = []

        self._zipfile = None
        self._init()

    def _init(self):
        if os.path.isfile(self.root_path) and zipfile.is_zipfile(self.root_path):
            self.is_initialized = self._init_from_zip()
        elif os.path.isdir(self.root_path) and os.path.exists(self.root_path):
            self.is_initialized = self._init_from_dir()
        else:
            self.is_initialized = False

    def _init_from_dir(self):
        for parent, dir_names, file_names in os.walk(self.root_path):
            rel = '' if parent == self.root_path else os.path.relpath(parent, self.root_path)
            for file_name in file_names:
                file = os.path.join(rel, file_name)
                self.namelist.append(file)
                name, ext = os.path.splitext(file_name)
                if ext in kikka.const.IMAGE_FORMATS:
                    self.image_list.append(file)
        return True

    def _init_from_zip(self):
        self._zipfile = zipfile.ZipFile(self.root_path, 'r')
        self.is_zip = True

        name, ext = os.path.splitext(os.path.basename(self.root_path))
        self.namelist = [file.replace(name + '/', '').replace('/', '\\') for file in self._zipfile.namelist()]
        if '' in self.namelist:
            self.namelist.remove('')

        for filename in self.namelist:
            name, ext = os.path.splitext(filename)
            if ext in kikka.const.IMAGE_FORMATS:
                self.image_list.append(filename)
        return True

    def get_fp(self, filename, mode, encoding='utf-8'):
        if filename.startswith(self.root_path):
            filename = os.path.relpath(filename, self.root_path)

        if filename not in self.namelist:
            return None

        if self.is_zip:
            name, ext = os.path.splitext(os.path.basename(self.root_path))
            filename = os.path.join(name, filename)
            filename = filename.replace('\\', '/')

            if 'b' in mode:
                mode = mode.replace('b', '')

            if mode not in ['r', 'w']:
                return None

            fp = self._zipfile.open(filename, mode)
        else:
            filename = os.path.join(self.root_path, filename)
            if 'b' in mode:
                fp = open(filename, mode)
            else:
                fp = open(filename, mode, encoding=encoding)
        return fp

    def get_image(self, filename):
        fp = self.get_fp(filename, 'rb')
        if fp:
            data = fp.read()
            img = QImage.fromData(data)
            if img:
                return img

        logging.warning("Image lost: %s" % filename)
        return kikka.helper.get_default_image()



