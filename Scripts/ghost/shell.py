import os
import re
import logging
import collections
from enum import Enum
from PyQt5.QtCore import QPoint, QRect

from kikka.fileloader import FileLoader
from ghost.struct import AuthorInfo, ShellMenuStyle, ShellSetting, BindGroup
from kikka.const import WindowConst, SurfaceNameEnum
from .struct import Element, CollisionBox, AnimationData, Pattern, EPatternType


class Shell(FileLoader):
    def __init__(self, root_path):
        FileLoader.__init__(self, root_path)
        self.is_loaded = False

        self.name = ''
        self.type = 'shell'
        self.catalog = 'Normal'
        self.version = 0
        self.max_width = 0
        self.description = ''
        self.unicode_name = ''
        self.author = AuthorInfo()
        self.collision_sort = 'none'
        self.animation_sort = 'descend'

        self.bind = {}
        self.alias = {}
        self.setting = {}
        self.shell_menu_style = ShellMenuStyle()

        self._surfaces = {}
        self._surfacesName = {}

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
        logging.info("load shell: %s", self.unicode_name)
        self._load_surfaces()
        self._load_surface_table()
        self._sort_data()
        self.is_loaded = True

    def reload(self):
        self.init()
        self.is_loaded = False
        self.load()

    def _open_surfaces(self, fp, map=None):
        surfaces_map = {} if map is None else map
        surface_id = []

        the_line_is_key = True
        data_type = 0
        ALIAS_DATA = 1
        SURFACES_DATA = 2
        DESCRIPT_DATA = 3

        for line in fp:
            if isinstance(line, bytes):
                line = line.decode('utf-8')

            line = line.replace("\n", "").replace("\r", "")
            line = line.strip(' ')

            if line == '' or line.find(r'\\') == 0 or line.find('//') == 0 or line.find('#') == 0:
                continue

            if line == '{':
                the_line_is_key = False
                continue

            if line == '}':
                the_line_is_key = True
                surface_id = []
                continue

            if the_line_is_key is False:
                # set value
                if data_type == SURFACES_DATA:
                    for id in surface_id:
                        surfaces_map[id].append(line)
                elif data_type == ALIAS_DATA:
                    index = line.index(',')
                    id = int(line[0:index])
                    arr = line[index + 2:-1].split(',')
                    irr = [int(i) for i in arr]
                    self.alias[id] = irr
                elif data_type == DESCRIPT_DATA:
                    keys = line.replace(' ', '').split(',')
                    if keys[0] == 'version':
                        self.version = int(keys[1])
                    elif keys[0] == 'maxwidth':
                        self.max_width = int(keys[1])
                    elif keys[0] == 'collision-sort' and keys[1] in ['none', 'ascend', 'descend']:
                        self.collision_sort = keys[1]
                    elif keys[0] == 'animation-sort' and keys[1] in ['ascend', 'descend']:
                        self.animation_sort = keys[1]
                    else:
                        self._ignore_params(keys[0], keys[1])
            else:
                # check struct ID
                if 'descript' in line:
                    data_type = DESCRIPT_DATA
                    continue

                if 'alias' in line:
                    data_type = ALIAS_DATA
                    continue

                data_type = SURFACES_DATA
                keys = line.replace('surface', '').replace(' ', '').split(',')
                for key in keys:
                    if key == '':
                        continue
                    if key[0] == '!':
                        # remove ID
                        key = key[1:]
                        if '-' in key:
                            v = key.split('-')
                            a = int(v[0])
                            b = int(v[1])
                            for id in range(a, b):
                                if id in surfaces_map:
                                    surface_id.remove(id)
                                    surfaces_map.pop(id)
                        else:
                            id = int(key)
                            surface_id.remove(id)
                            surfaces_map.pop(id)
                    else:
                        # add ID
                        if '-' in key:
                            v = key.split('-')
                            a = int(v[0])
                            b = int(v[1])
                            for id in range(a, b):
                                if id not in surfaces_map:
                                    surface_id.append(id)
                                    surfaces_map[id] = []
                        else:
                            id = int(key)
                            surface_id.append(id)
                            if id not in surfaces_map:
                                surfaces_map[id] = []
                    pass
                pass  # exit for
            pass
        pass  # exit for
        return surfaces_map

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

        for keys, values in map.items():
            key = keys.split('.')
            value = values.split(',')

            if key[0] == 'menu':
                if len(key) == 1:
                    self.shell_menu_style.hidden = True
                elif key[1] == 'font':
                    if key[2] == 'name':
                        self.shell_menu_style.font_family = value[0]
                    elif key[2] == 'height':
                        self.shell_menu_style.font_size = int(value[0])
                    else:
                        self._ignore_params(keys, values)
                elif key[1] == 'background':
                    if key[2] == 'font' and key[3] == 'color':
                        if key[4] == 'r':
                            self.shell_menu_style.bg_font_color[0] = int(value[0])
                        elif key[4] == 'g':
                            self.shell_menu_style.bg_font_color[1] = int(value[0])
                        elif key[4] == 'b':
                            self.shell_menu_style.bg_font_color[2] = int(value[0])
                        else:
                            self._ignore_params(keys, values)
                    elif key[2] == 'bitmap' and key[3] == 'filename':
                        self.shell_menu_style.bg_image = value[0]
                    elif key[2] == 'alignment':
                        self.shell_menu_style.background_alignment = value[0]
                    else:
                        self._ignore_params(keys, values)
                elif key[1] == 'foreground':
                    if key[2] == 'font' and key[3] == 'color':
                        if key[4] == 'r':
                            self.shell_menu_style.fg_font_color[0] = int(value[0])
                        elif key[4] == 'g':
                            self.shell_menu_style.fg_font_color[1] = int(value[0])
                        elif key[4] == 'b':
                            self.shell_menu_style.fg_font_color[2] = int(value[0])
                        else:
                            self._ignore_params(keys, values)
                    elif key[2] == 'bitmap' and key[3] == 'filename':
                        self.shell_menu_style.fg_image = value[0]
                    elif key[2] == 'alignment':
                        self.shell_menu_style.foreground_alignment = value[0]
                    else:
                        self._ignore_params(keys, values)
                elif key[1] == 'disable':
                    if key[2] == 'font' and key[3] == 'color':
                        if key[4] == 'r':
                            self.shell_menu_style.disable_font_color[0] = int(value[0])
                        elif key[4] == 'g':
                            self.shell_menu_style.disable_font_color[1] = int(value[0])
                        elif key[4] == 'b':
                            self.shell_menu_style.disable_font_color[2] = int(value[0])
                        else:
                            self._ignore_params(keys, values)
                elif key[1] == 'separator':
                    if key[2] == 'color':
                        if key[3] == 'r':
                            self.shell_menu_style.separator_color[0] = int(value[0])
                        elif key[3] == 'g':
                            self.shell_menu_style.separator_color[1] = int(value[0])
                        elif key[3] == 'b':
                            self.shell_menu_style.separator_color[2] = int(value[0])
                        else:
                            self._ignore_params(keys, values)
                elif key[1] == 'sidebar':
                    if key[2] == 'bitmap' and key[3] == 'filename':
                        self.shell_menu_style.sidebar_image = value[0]
                    elif key[2] == 'alignment':
                        self.shell_menu_style.sidebar_alignment = value[0]
                    else:
                        self._ignore_params(keys, values)
                else:
                    self._ignore_params(keys, values)

            elif key[0] in ['sakura', 'kero'] or key[0:4] == 'char':
                if key[0] == 'sakura':
                    sid = 0
                elif key[0] == 'kero':
                    sid = 1
                else:
                    sid = int(key[5:])

                if sid not in self.setting.keys():
                    self.setting[sid] = ShellSetting()

                if 'bindgroup' in key[1]:
                    aid = int(key[1][9:])
                    if key[2] == 'name':
                        img = '' if len(value) < 3 else value[2]
                        self.setting[sid].bind_groups[aid] = BindGroup(aid, value[0], value[1], img)
                    elif key[2] == 'default':
                        self.setting[sid].bind_groups[aid].set_default(value[0])
                    else:
                        self._ignore_params(keys, values)
                elif 'menuitem' in key[1]:
                    mid = int(key[1][8:])
                    if value[0] != '-':
                        self.setting[sid].clothes_menu[mid] = int(value[0])
                    else:
                        self.setting[sid].clothes_menu[mid] = -1
                elif key[1] == 'balloon':
                    if key[2] == 'offsetx':
                        self.setting[sid].balloon_offset.setX(int(value[0]))
                    elif key[2] == 'offsety':
                        self.setting[sid].balloon_offset.setY(int(value[0]))
                    elif key[2] == 'alignment':
                        self.setting[sid].balloon_alignment = value[0]
                    else:
                        self._ignore_params(keys, values)
                elif 'bindoption' in key[1]:
                    # gid = int(key[1][10:])
                    if key[2] == 'group':
                        self.setting[sid].bind_option[value[0]] = value[1]
                    else:
                        self._ignore_params(keys, values)
                elif 'defaultx' in key[1]:
                    self.setting[sid].offset.setX(int(value[0]))
                elif 'defaulty' in key[1]:
                    self.setting[sid].offset.setY(int(value[0]))
                elif 'defaultleft' in key[1]:
                    self.setting[sid].position.setX(int(value[0]))
                elif 'defaulttop' in key[1]:
                    self.setting[sid].position.setY(int(value[0]))
                else:
                    self._ignore_params(keys, values)

            elif key[0] == 'id':
                self.name = value[0]
            elif key[0] == 'name':
                self.unicode_name = value[0]
            elif key[0] == 'catalog':
                self.catalog = value[0]
            elif key[0] == 'description':
                self.description = value[0]
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
            elif key[0] == 'charset' \
                    or key[0] == 'shiori' \
                    or key[0] == 'mode' \
                    or key[0] == 'seriko':
                # self._IgnoreParams(keys, values)
                pass

            # unknown params
            else:
                self._ignore_params(keys, values)
        pass

    def _load_surface_table(self):
        if self.is_zip:
            name, ext = os.path.splitext(os.path.basename(self.root_path))
            filename = os.path.join(name, 'surfacetable.txt')
        else:
            filename = os.path.join(self.root_path, 'surfacetable.txt')

        fp = self.get_fp(filename, 'r')
        if fp is None:
            return False

        for line in fp:
            if isinstance(line, bytes):
                line = line.decode('utf-8')

            line = line.replace("\n", "").replace("\r", "")
            line = line.strip(' ')

            if line == '' or line.find(r'\\') == 0 or line.find('//') == 0 or line.find('#') == 0:
                continue

            try:
                keys = line.replace(' ', '').split(',')
                ID = int(keys[0])
                if ID in self._surfaces:
                    self._surfaces[ID].unicode_name = keys[1]
            except Exception:
                continue
        pass  # exit for
        fp.close()
        return True

    def _load_surfaces(self):
        i = 2
        if self.is_zip:
            name, ext = os.path.splitext(os.path.basename(self.root_path))
            fp = self.get_fp('surfaces.txt', 'r')
            if fp is None:
                return False

            surfaces_map = self._open_surfaces(fp)
            fp.close()

            while True:
                fp = self.get_fp('surfaces%d.txt' % i, 'r')
                if fp is None:
                    break

                surfaces_map = self._open_surfaces(fp, surfaces_map)
                fp.close()
                i = i + 1
        else:
            filename = os.path.join(self.root_path, 'surfaces.txt')
            fp = self.get_fp(filename, 'r')
            if fp is None:
                return False

            surfaces_map = self._open_surfaces(fp)
            fp.close()

            while True:
                filename = os.path.join(self.root_path, 'surfaces%d.txt' % i)
                fp = self.get_fp(filename, 'r')
                if fp is None:
                    break

                surfaces_map = self._open_surfaces(fp, surfaces_map)
                fp.close()
                i = i + 1

        for key, values in surfaces_map.items():
            self._surfaces[key] = Surface(key, values)
        return True

    def _ignore_params(self, key, values):
        logging.info('unknown shell params: %s,%s' % (key, values))
        pass

    def _sort_data(self):
        def _sort(item, reverse=False):
            return collections.OrderedDict(sorted(item, key=lambda t: t[0], reverse=reverse))

        self._surfaces = _sort(self._surfaces.items())
        for sid, surface in self._surfaces.items():
            self._surfaces[sid].elements = _sort(surface.elements.items())
            self._surfaces[sid].animations = _sort(surface.animations.items(), self.animation_sort == 'ascend')
            if self.collision_sort != 'none':
                ascend = self.collision_sort == 'ascend'
                self._surfaces[sid].collision_boxes = _sort(surface.collision_boxes.items(), ascend)

        self._surfacesName = {}
        for sid, surface in self._surfaces.items():
            self._surfacesName[sid] = (surface.name, surface.unicode_name)

    def get_surface(self, surfaces_id):
        if surfaces_id in self._surfaces:
            return self._surfaces[surfaces_id]
        else:
            logging.error("getSurface: surfaceID: %d NOT exist" % surfaces_id)
            return None

    def get_surface_name_list(self):
        return self._surfacesName

    def get_collision_boxes(self, surfaces_id):
        return self._surfaces[surfaces_id].collision_boxes if surfaces_id in self._surfaces else {}

    def get_offset(self, soul_id):
        return self.setting[soul_id].offset

    def get_shell_menu_style(self):
        return self.shell_menu_style

    def add_bind(self, soul_id, aid):
        if soul_id not in self.bind.keys():
            self.bind[soul_id] = []

        if aid not in self.bind[soul_id]:
            self.bind[soul_id].append(aid)
            self.bind[soul_id].sort()

    def get_bind(self, soul_id):
        if soul_id not in self.bind.keys():
            self.bind[soul_id] = []
        return self.bind[soul_id]

    def set_clothes(self, soul_id, aid, is_enable=True):
        if soul_id not in self.bind.keys():
            self.bind[soul_id] = []

        if is_enable is True and aid not in self.bind[soul_id]:
            self.add_bind(soul_id, aid)
        elif is_enable is False and aid in self.bind[soul_id]:
            self.bind[soul_id].remove(aid)


class Surface:
    def __init__(self, id, values):
        self.id = id
        self.name = SurfaceNameEnum[id] if id in SurfaceNameEnum.keys() else 'Surface%d' % id
        self.unicode_name = None
        self.elements = {}
        self.animations = {}
        self.collision_boxes = {}
        self.rect = QRect()

        self.base_pos = QPoint(WindowConst.UNSET)
        self.surface_center = QPoint(WindowConst.UNSET)
        self.kinoko_center = QPoint(WindowConst.UNSET)

        self._load_surface(values)

    def _load_surface(self, values):
        for line in values:
            if line == "":
                continue

            matchtype, params = SurfaceMatchLine.match_line(line)
            if matchtype == SurfaceMatchLine.Unknown:
                logging.warning("NO Match Line: %s", line)

            elif matchtype == SurfaceMatchLine.Elements:
                self.elements[int(params[0])] = Element(params)

            elif matchtype == SurfaceMatchLine.CollisionBoxes:
                self.collision_boxes[int(params[0])] = CollisionBox(params)

            elif matchtype == SurfaceMatchLine.AnimationInterval:
                aid = int(params[0])
                ani = AnimationData(aid, self.animations) if aid not in self.animations else self.animations[aid]
                if ',' in params[1]:
                    p = params[1].split(',')
                    ani.interval = p[0]
                    ani.interval_value = float(p[1])
                else:
                    ani.interval = params[1]
                    ani.interval_value = 0
                self.animations[aid] = ani

            elif matchtype == SurfaceMatchLine.AnimationPattern:
                aid = int(params[0])
                ani = AnimationData(aid, self.animations) if aid not in self.animations else self.animations[aid]
                ani.patterns[int(params[1])] = Pattern(params, EPatternType.Normal)
                self.animations[aid] = ani

            elif matchtype == SurfaceMatchLine.AnimationPatternNew:
                aid = int(params[0])
                ani = AnimationData(aid, self.animations) if aid not in self.animations else self.animations[aid]
                ani.patterns[int(params[1])] = Pattern(params, EPatternType.New)
                self.animations[aid] = ani

            elif matchtype == SurfaceMatchLine.AnimationPatternAlternative:
                aid = int(params[0])
                ani = AnimationData(aid, self.animations) if aid not in self.animations else self.animations[aid]
                ani.patterns[int(params[1])] = Pattern(params, EPatternType.Alternative)
                self.animations[aid] = ani

            elif matchtype == SurfaceMatchLine.AnimationOptionExclusive:
                aid = int(params[0])
                ani = AnimationData(aid, self.animations) if aid not in self.animations else self.animations[aid]
                ani.exclusive = True
                self.animations[aid] = ani

            elif matchtype == SurfaceMatchLine.SurfaceCenterX:
                self.surface_center.setX(int(params[0]))

            elif matchtype == SurfaceMatchLine.SurfaceCenterY:
                self.surface_center.setY(int(params[0]))

            elif matchtype == SurfaceMatchLine.KinokoCenterX:
                self.kinoko_center.setX(int(params[0]))

            elif matchtype == SurfaceMatchLine.KinokoCenterY:
                self.kinoko_center.setY(int(params[0]))

            elif matchtype == SurfaceMatchLine.BasePosX:
                self.base_pos.setX(int(params[0]))

            elif matchtype == SurfaceMatchLine.BasePosX:
                self.base_pos.setY(int(params[0]))
        pass  # exit for


class SurfaceMatchLine(Enum):
    Unknown = 0
    Elements = 100

    AnimationInterval = 200
    AnimationPattern = 201
    AnimationPatternNew = 202
    AnimationPatternAlternative = 203
    AnimationOptionExclusive = 204

    CollisionBoxes = 300

    SurfaceCenterX = 401
    SurfaceCenterY = 402
    KinokoCenterX = 403
    KinokoCenterY = 404
    BasePosX = 405
    BasePosY = 406

    @staticmethod
    def match_line(line):

        # Element
        # element[ID],[PaintType],[filename],[X],[Y]
        res = re.match(
            r'^element(\d+),(base|overlay|overlayfast|replace|interpolate|asis|move|bind|add|reduce|insert),'
            r'(\w+.png),(\d+),(\d+)$',
            line)
        if res is not None:
            return SurfaceMatchLine.Elements, res.groups()

        # Animation Interval
        # [aID]interval,[interval]
        res = re.match(
            r'^(?:animation)?(\d+).?interval,(sometimes|rarely|random,\d+|periodic,'
            r'\d+[.][0-9]*|always|runonce|never|yen-e|talk,\d+|bind)$',
            line)
        if res is not None:
            return SurfaceMatchLine.AnimationInterval, res.groups()

        # Animation Pattern Alternative
        # [aID]pattern[pID],[surfaceID],[time],[methodType],[[aID1], [aID2], ...]
        res = re.match(
            r'^(\d+)pattern(\d+),(\-?\d+),(\d+),(insert|start|stop|alternativestart|alternativestop),'
            r'(?:[\[\(]?((?:\d+[\.\,])*\d+)[\]\)]?)$',
            line)
        if res is not None:
            return SurfaceMatchLine.AnimationPatternAlternative, res.groups()

        # Animation Pattern Normal
        # [aID]pattern[pID],[surfaceID],[time],[methodType],[X],[Y]
        res = re.match(
            r'^(\d+)pattern(\d+),(\-?\d+),(\d+),'
            r'(base|overlay|overlayfast|replace|interpolate|asis|move|bind|add|reduce),(\-?\d+),(\-?\d+)$',
            line)
        if res is not None:
            return SurfaceMatchLine.AnimationPattern, res.groups()

        # Animation Pattern New
        # animation[aID].pattern[pID],[methodType],[surfaceID],[time],[X],[Y]
        res = re.match(
            r'^animation(\d+).pattern(\d+),(base|overlay|overlayfast|replace|interpolate|asis|move|bind|add|reduce),'
            r'(\-?\d+),(\d+),(\-?\d+),(\-?\d+)$',
            line)
        if res is not None:
            return SurfaceMatchLine.AnimationPatternNew, res.groups()

        # Animation Option exclusive
        # [aID]option,exclusive
        res = re.match(r'^(\d+)option,exclusive$', line)
        if res is not None:
            return SurfaceMatchLine.AnimationOptionExclusive, res.groups()

        # CollisionBox
        # Collision[cID],[sX],[sY],[eX],[eY],[Tag]
        res = re.match(r'^collision(\d+),(\d+),(\d+),(\d+),(\d+),(\w+)$', line)
        if res is not None:
            return SurfaceMatchLine.CollisionBoxes, res.groups()

        # Surface Center X
        # point.centerx,[int]
        res = re.match(r'^point.centerx,(\d+)$', line)
        if res is not None:
            return SurfaceMatchLine.SurfaceCenterX, res.groups()

        # Surface Center Y
        # point.centery,[int]
        res = re.match(r'^point.centery,(\d+)$', line)
        if res is not None:
            return SurfaceMatchLine.SurfaceCenterY, res.groups()

        # Kinoko Center X
        # point.kinoko.centerx,[int]
        res = re.match(r'^point.kinoko.centerx,(\d+)$', line)
        if res is not None:
            return SurfaceMatchLine.KinokoCenterX, res.groups()

        # Kinoko Center Y
        # point.kinoko.centery,[int]
        res = re.match(r'^point.kinoko.centery,(\d+)$', line)
        if res is not None:
            return SurfaceMatchLine.KinokoCenterY, res.groups()

        # basepos X
        # point.base_pos.centerx,[int]
        res = re.match(r'^point.base_pos.centerx,(\d+)$', line)
        if res is not None:
            return SurfaceMatchLine.BasePosX, res.groups()

        # basepos Y
        # point.base_pos.centery,[int]
        res = re.match(r'^point.base_pos.centery,(\d+)$', line)
        if res is not None:
            return SurfaceMatchLine.BasePosY, res.groups()

        # Unknown
        return SurfaceMatchLine.Unknown, None

    pass

