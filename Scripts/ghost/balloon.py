# coding=utf-8
import os
import logging

from PyQt5.QtCore import QRect, QPoint, QSize

import kikka
from ghost.struct import AuthorInfo
from kikka.fileloader import FileLoader


class Balloon(FileLoader):
    def __init__(self, root_path):
        FileLoader.__init__(self, root_path)
        self.is_loaded = False

        self.name = ''
        self.type = ''
        self.unicode_name = ''
        self.author = AuthorInfo()

        self.bg_rect = []
        self.clip_width = []
        self.clip_height = []

        self.stylesheet = None
        self.no_flip_center = False
        self.flip_background = False
        self.minimum_size = kikka.const.WindowConst.DialogWindowDefaultSize
        self.margin = kikka.const.WindowConst.DialogWindowDefaultMargin

        self.init()

    def __del__(self):
        if self._zipfile:
            self._zipfile.close()
            self._zipfile = None

    def init(self):
        fp = self.get_fp('descript.txt', 'r')
        if fp is None:
            self.is_initialized = False
            return False
        self._load_descript(fp)
        fp.close()

        if self.name == '':
            self.name = os.path.basename(self.root_path)

    def load(self):
        if self.is_loaded:
            return

        logging.info("load balloon: %s", self.unicode_name)
        self._load_stylesheet()

        # load rect
        srect = []
        sw = self.clip_width
        sh = self.clip_height
        for y in range(len(self.clip_height)):
            sr = []
            for x in range(len(self.clip_width)):
                pt = QPoint(0, 0)
                if x > 0:
                    pt.setX(sr[x - 1].x() + sw[x - 1])
                if y > 0:
                    pt.setY(srect[y - 1][0].y() + sh[y - 1])
                sz = QSize(sw[x], sh[y])
                sr.append(QRect(pt, sz))
                pass
            srect.append(sr)
        pass  # exit for

        self.bg_rect = srect
        self.is_loaded = True

    def _load_descript(self, fp):
        map = {}
        for line in fp:
            if isinstance(line, bytes):
                line = line.decode('utf-8')

            line = line.replace("\n", "").replace("\r", "")
            line = line.strip(' ')

            if line == '' or line.find('\\') == 0 or line.find('//') == 0 or line.find('#') == 0:
                continue

            index = line.index(',')

            key = line[0:index]
            value = line[index + 1:]

            map[key] = value
        pass  # exit for

        # load key from descript.txt
        for keys, values in map.items():
            key = keys.split('.')
            value = values.split(',')

            if key[0] == 'clip':
                grid = int(value[0])
                if key[1] == 'width':
                    if grid == 3 and len(value) == 4:
                        self.clip_width = [int(value[1]), int(value[2]), int(value[3])]
                    elif grid == 5 and len(value) == 6:
                        self.clip_width = [int(value[1]), int(value[2]), int(value[3]), int(value[4]), int(value[5])]
                elif key[1] == 'height':
                    if grid == 3 and len(value) == 4:
                        self.clip_height = [int(value[1]), int(value[2]), int(value[3])]
                    elif grid == 5 and len(value) == 6:
                        self.clip_height = [int(value[1]), int(value[2]), int(value[3]), int(value[4]), int(value[5])]
                else:
                    self._ignore_params(keys, values)

            elif key[0] == 'minimumsize':
                self.minimum_size = QSize(int(value[0]), int(value[1]))
            elif key[0] == 'flipbackground':
                self.flip_background = int(value[0]) == 1
            elif key[0] == 'noflipcenter':
                self.no_flip_center = int(value[0]) == 1
            elif key[0] == 'margin':
                self.margin = [int(value[0]), int(value[1]), int(value[2]), int(value[3])]

            elif key[0] == 'name':
                self.name = value[0]
            elif key[0] == 'unicode_name':
                self.unicode_name = value[0]
            elif key[0] == 'type':
                self.type = value[0]
            elif key[0] == 'craftman' or key[0] == 'craftmanw':
                self.author.name = value[0]
            elif key[0] == 'crafmanurl':
                self.author.website = value[0]
            elif key[0] == 'homeurl':
                self.author.update_url = value[0]
            elif key[0] == 'readme':
                self.author.readme = value[0]

            # skip params
            elif key[0] == 'charset':
                # self._ignore_params(keys, values)
                pass

            # unknown params
            else:
                self._ignore_params(keys, values)
        pass  # exit for

    def _load_stylesheet(self):
        fp = self.get_fp('stylesheet.qss', 'r')
        self.stylesheet = fp.read()
        if isinstance(self.stylesheet, bytes):
            self.stylesheet = self.stylesheet.decode('utf-8')
        fp.close()

    def _ignore_params(self, key, values):
        print('unknown shell params: %s,%s' % (key, values))
