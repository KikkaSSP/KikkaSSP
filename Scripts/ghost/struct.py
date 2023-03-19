from enum import Enum
from kikka.const import WindowConst, SurfaceNameEnum
from PyQt5.QtCore import QPoint, QRect
from collections import OrderedDict


class AuthorInfo:
    def __init__(self):
        self.name = ''
        self.website = ''
        self.update_url = ''
        self.readme = ''


class ShellSetting:
    def __init__(self):
        self.name = ''
        self.offset = QPoint(0, 0)
        self.position = QPoint(WindowConst.UNSET)
        self.balloon_offset = QPoint(0, 0)
        self.balloon_alignment = 'lefttop'
        self.bind_option = {}
        self.bind_groups = {}
        self.clothes_menu = {}


class ShellMenuStyle:
    def __init__(self):
        self.hidden = False

        self.font_family = ''
        self.font_size = -1

        self.bg_image = ''
        self.bg_font_color = [-1, -1, -1]
        self.background_alignment = 'lefttop'

        self.fg_image = ''
        self.fg_font_color = [-1, -1, -1]
        self.foreground_alignment = 'lefttop'

        self.disable_font_color = [-1, -1, -1]
        self.separator_color = [-1, -1, -1]

        self.sidebar_image = ''
        self.sidebar_alignment = 'lefttop'


class BindGroup:
    def __init__(self, animation_id, type, title, image=''):
        self.animation_id = animation_id
        self.type = type
        self.title = title
        self.image = image
        self.default = False

    def set_default(self, boolean):
        self.default = False if boolean == '0' else True


class Element:
    def __init__(self, params):
        self.id = int(params[0])
        self.paint_type = params[1]
        self.filename = params[2]
        self.offset = QPoint(int(params[3]), int(params[4]))


class CollisionBox:
    def __init__(self, params):
        self.id = int(params[0])
        self.rect = QRect(int(params[1]),
                          int(params[2]),
                          int(params[3]) - int(params[1]),
                          int(params[4]) - int(params[2]))
        self.tag = params[5]


class AnimationData:
    def __init__(self, id, parent):
        self._parent = parent
        self.id = id
        self.interval = 'never'
        self.interval_value = 0
        self.exclusive = False
        self.patterns = OrderedDict()


class EPatternType(Enum):
    Normal = 0
    New = 1
    Alternative = 2


class Pattern:
    def __init__(self, params, match_type=EPatternType.Normal):
        self.bind_animation = -1
        if match_type == EPatternType.Normal:
            self.id = int(params[1])
            self.method_type = params[4]
            self.surface_id = int(params[2])
            self.time = int(params[3]) * 10
            self.offset = QPoint(int(params[5]), int(params[6]))
            self.aid = [-1]
        elif match_type == EPatternType.New:
            self.id = int(params[1])
            self.method_type = params[2]
            self.surface_id = int(params[3])
            self.time = int(params[4])
            self.offset = QPoint(int(params[5]), int(params[6]))
            self.aid = [-1]
        elif match_type == EPatternType.Alternative:
            self.id = int(params[1])
            self.method_type = params[4]
            self.surface_id = int(params[2])
            self.time = int(params[3])
            self.offset = QPoint()
            if '.' in params[5]:
                self.aid = list(map(int, params[5].split('.')))
            elif ',' in params[5]:
                self.aid = list(map(int, params[5].split(',')))
            else:
                self.aid = [int(params[5])]

    def is_control_pattern(self):
        return self.method_type in ['alternativestart', 'start', 'insert', 'alternativestop', 'stop']


