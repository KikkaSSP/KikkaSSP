# coding=utf-8
import os
import sys
import six
import copy
import hashlib
import logging

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QApplication

import kikka


class MetaSingleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instance


class Singleton(six.with_metaclass(MetaSingleton)):
    """Singleton class definition."""
    @classmethod
    def instance(cls):
        return cls()


class GhostEventParam:
    def __init__(self, ghost_id, soul_id=0, event_type=0, event_tag='', data=None):
        self.ghost_id = ghost_id
        self.soul_id = soul_id
        self.event_type = event_type
        self.event_tag = event_tag
        self.data = {} if data is None else data

    def copy(self):
        return GhostEventParam(self.ghost_id, self.soul_id, self.event_type, self.event_tag, copy.deepcopy(self.data))


class KikkaHelper(Singleton):
    _instance = None

    def __init__(self):
        fn = os.path.join(kikka.path.IMAGE, "default.png")
        if os.path.exists(fn):
            self._default_image = QImage(fn)
        else:
            self._default_image = QImage(1, 1, QImage.Format_RGBA8888)

    @staticmethod
    def check_encoding(filepath):
        CODES = ['UTF-8', 'GBK', 'Shift-JIF', 'GB18030', 'BIG5', 'UTF-16']

        # UTF-8 BOM前缀字节
        UTF_8_BOM = b'\xef\xbb\xbf'

        f = None
        b = ""
        file_code = None
        for code in CODES:
            try:
                f = open(filepath, 'rb')
                b = f.read()
                b.decode(encoding=code)
                f.close()
                file_code = code
                break
            except Exception:
                f.close()
                continue

        if 'UTF-8' == file_code and b.startswith(UTF_8_BOM):
            file_code = 'UTF-8-SIG'

        if file_code is None:
            raise SyntaxError('Unknown file encoding: %s' % filepath)

        return file_code

    @staticmethod
    def get_screen_resolution():
        rect = QApplication.instance().desktop().screenGeometry()
        return (rect.width(), rect.height())

    @staticmethod
    def get_screen_client_rect():
        rect = QApplication.instance().desktop().availableGeometry()
        return (rect.width(), rect.height())

    def get_default_image(self):
        return QImage(self._default_image)

    def get_image(self, filepath):
        if os.path.exists(filepath):
            return QImage(filepath)
        else:
            logging.warning("Image lost: %s" % filepath)
            return QImage(self._default_image)

    @staticmethod
    def draw_image(destImage, srcImage, x, y, drawtype):
        if destImage is None or srcImage is None:
            return

        if drawtype == 'base' or drawtype == 'overlay':
            mode = QPainter.CompositionMode_SourceOver
        elif drawtype == 'overlayfast':
            mode = QPainter.CompositionMode_SourceAtop
        elif drawtype == 'replace':
            mode = QPainter.CompositionMode_Source
        elif drawtype == 'interpolate':
            mode = QPainter.CompositionMode_DestinationOver
        elif drawtype == 'asis':
            mode = QPainter.CompositionMode_DestinationAtop
        else:
            mode = QPainter.CompositionMode_SourceOver

        painter = QPainter(destImage)
        painter.setCompositionMode(mode)
        painter.drawImage(QPoint(x, y), srcImage)
        painter.end()

    @staticmethod
    def get_md5(s):
        md5 = hashlib.md5()
        md5.update(s.encode())
        return md5.hexdigest()

    @staticmethod
    def get_short_md5(s):
        md5 = hashlib.md5()
        md5.update(s.encode())
        return md5.hexdigest()[8:24]

    @staticmethod
    def make_ghost_event_param(ghost_id, soul_id=0, event_type=0, event_tag='', data=None):
        return GhostEventParam(ghost_id, soul_id, event_type, event_tag, data)
