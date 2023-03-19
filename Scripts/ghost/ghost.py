# coding=utf-8
import os
import time
import logging
import datetime

from collections import OrderedDict
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPainter, QColor, QPixmap

import kikka
from ghost.soul import Soul
from kikka.menu import MenuStyle
from kikka.const import GhostEvent
from kikka.helper import GhostEventParam
from ghost.window_dialog import WindowDialog
from ghost.sakura_script import SakuraScript


class KikkaGhostSignal(QObject):
    GhostEvent = pyqtSignal(GhostEventParam)


class Ghost:
    def __init__(self, gid, ghost_data, ghost_loader):
        self.is_loaded = False

        self.id = gid
        self.name = ghost_data.get("config").get("name")
        self._loader = ghost_loader

        self.initialized = False
        self.signal = KikkaGhostSignal()
        self._souls = OrderedDict()

        self._shell = None
        self._shells = []
        self._name2shell_id = {}
        self._shell_image = {}

        self._balloon = None
        self._balloons = []
        self._name2balloon_id = {}
        self._balloon_image = {}
        self._balloon_image_cache = None

        self._menu_style = None
        self._is_lock_on_task_bar = True

        self._event_list = {}
        self._last_talk_time = self._now()
        self._talk_speed = 50
        self._ending_wait = 5000
        self._is_talking = False
        self._tokens = []
        self._current_talk_soul = 0
        self._script_wait = 0
        self._variables = {}
        self._datetime = datetime.datetime.now()

    def init(self):
        # load resource
        shell_path = os.path.join(self._loader.root_path, "Resource", "Shell")
        self._shells, self._name2shell_id = kikka.ghost.scan_shell(shell_path)

        balloon_path = os.path.join(self._loader.root_path, "Resource", "Balloon")
        self._balloons, self._name2balloon_id = kikka.ghost.scan_balloon(balloon_path)

        # create ghost table
        kikka.memory.create_table(str('ghost_' + self.name))

        # update boot time
        boot_last = datetime.datetime.fromtimestamp(self.memory_read('BootThis', time.time()))
        boot_this = datetime.datetime.now()
        self.memory_write('BootLast', boot_last.timestamp())
        self.memory_write('BootThis', boot_this.timestamp())

        # get option
        self.set_shell(self.memory_read('CurrentShellName', ''))
        self.set_balloon(self.memory_read('CurrentBalloonName', ''))
        self.set_is_lock_on_task_bar(self.memory_read('isLockOnTaskBar', True))
        self.signal.GhostEvent.connect(self.ghost_event)

        self._variables['selfname'] = self.name
        self._variables['selfname2'] = ''
        self._variables['keroname'] = ''

        self._variables['username'] = self.memory_read('UserName', '')
        if self._variables['username'] == '':
            self._variables['username'] = 'A.A君'
        self.initialized = True

    def initialed(self):
        for soul in self._souls.values():
            soul.initialed()

    # soul ###################################################################################

    def add_soul(self, soul_id, surface_id=0):
        if soul_id in self._souls.keys():
            logging.error("addSoul: the soul ID %d exits" % soul_id)
            return None
        self._souls[soul_id] = Soul(self, soul_id, surface_id)
        return self._souls[soul_id]

    def get_soul(self, soul_id):
        return self._souls[soul_id] if soul_id in self._souls.keys() else None

    def get_soul_count(self):
        return len(self._souls)

    # shell ###################################################################################

    def change_shell(self, shell_name):
        self.hide()
        self.set_shell(shell_name)
        self.show()

    def reload_shell(self, shell_name=None):
        if shell_name is None:
            shell_name = self._shell.name
        shell = self.get_shell_by_name(shell_name)
        if shell is None:
            shell = self.get_shell(0)
            if shell is None:
                raise ValueError("setShell: load defalut shell fail.")

        self._shell = shell
        self._shell.load()
        self._shell_image = {}
        for filename in self._shell.image_list:
            p = os.path.join(self._shell.root_path, filename)
            self._shell_image[filename] = self._shell.get_image(p)
        self._menu_style = MenuStyle(self._shell.shell_menu_style, self._shell_image)

        for sid, soul in self._souls.items():
            soul.set_surface(-1)
            soul.update_clothes_menu()
            soul.move(soul.pos())

    def set_shell(self, shell_name):
        if self._shell is not None and self._shell.name == shell_name:
            return
        self.reload_shell(shell_name)
        self.memory_write('CurrentShellName', self._shell.name)

    def get_current_shell(self):
        return self._shell

    def get_shell(self, shell_id):
        if 0 <= shell_id < len(self._shells):
            return self._shells[shell_id]

        logging.warning("get_shell: index=%d NOT in shell list" % shell_id)
        return None

    def get_shell_by_name(self, shell_name):
        if shell_name in self._name2shell_id:
            return self._shells[self._name2shell_id[shell_name]]
        logging.warning("get_shell_by_name: '%s' NOT in shell list" % shell_name)
        return None

    def get_shell_count(self):
        return len(self._shells)

    # surface ###################################################################################

    def get_balloon_image(self, size: QSize, flip=False, soul_id=-1):
        if self._balloon is None:
            logging.warning("getBalloonImage: balloon is None")
            return kikka.helper.get_default_image()

        # calculate destination rect
        if len(self._balloon.clip_width) == 3:
            dw = [self._balloon.clip_width[0],
                  size.width() - self._balloon.clip_width[0] - self._balloon.clip_width[2],
                  self._balloon.clip_width[2]]
        elif len(self._balloon.clip_width) == 5:
            sw = size.width() - self._balloon.clip_width[0] - self._balloon.clip_width[2] - self._balloon.clip_width[4]
            dw = [self._balloon.clip_width[0],
                  sw // 2,
                  self._balloon.clip_width[2],
                  sw - sw // 2,
                  self._balloon.clip_width[4]]
        else:
            sw = size.width() // 3
            dw = [sw, size.width() - sw*2, sw]

        if len(self._balloon.clip_height) == 3:
            dh = [self._balloon.clip_height[0],
                  size.height() - self._balloon.clip_height[0] - self._balloon.clip_height[2],
                  self._balloon.clip_height[2]]
        elif len(self._balloon.clip_height) == 5:
            sh = size.height() \
                 - self._balloon.clip_height[0] \
                 - self._balloon.clip_height[2] \
                 - self._balloon.clip_height[4]
            dh = [self._balloon.clip_height[0],
                  sh // 2,
                  self._balloon.clip_height[2],
                  sh - sh // 2,
                  self._balloon.clip_height[4]]
        else:
            sh = size.height() // 3
            dh = [sh, size.height() - sh*2, sh]

        destination_rect = []
        for y in range(len(self._balloon.clip_height)):
            dr = []
            for x in range(len(self._balloon.clip_width)):
                pt = QPoint(0, 0)
                if x > 0:
                    pt.setX(dr[x-1].x() + dw[x-1])
                if y > 0:
                    pt.setY(destination_rect[y-1][0].y() + dh[y-1])
                sz = QSize(dw[x], dh[y])
                dr.append(QRect(pt, sz))
            destination_rect.append(dr)
        pass  # exit for

        # paint balloon image
        img = QImage(size, QImage.Format_ARGB32)
        pix_map = QPixmap().fromImage(self._balloon_image_cache, Qt.AutoColor)
        painter = QPainter(img)
        painter.setCompositionMode(QPainter.CompositionMode_Source)

        for y in range(len(self._balloon.clip_height)):
            for x in range(len(self._balloon.clip_width)):
                painter.drawPixmap(destination_rect[y][x], pix_map, self._balloon.bg_rect[y][x])
        painter.end()

        # flip or not
        if self._balloon.flip_background is True and flip is True:
            img = img.mirrored(True, False)
            if self._balloon.no_flip_center is True \
                    and len(self._balloon.clip_width) == 5 \
                    and len(self._balloon.clip_height) == 5:
                painter = QPainter(img)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.drawPixmap(destination_rect[2][2], pix_map, self._balloon.bg_rect[2][2])
                painter.end()

        # debug draw
        if kikka.ghost.isDebug is True:
            painter = QPainter(img)
            painter.fillRect(QRect(0, 0, 200, 64), QColor(0, 0, 0, 64))
            painter.setPen(Qt.red)
            for y in range(len(self._balloon.clip_height)):
                for x in range(len(self._balloon.clip_width)):
                    if x in (0, 2, 4) and y in (0, 2, 4):
                        continue
                    rect = QRect(destination_rect[y][x])
                    text = "(%d, %d)\n%d x %d" % (rect.x(), rect.y(), rect.width(), rect.height())
                    painter.drawText(rect, Qt.AlignCenter, text)
                if y > 0:
                    painter.drawLine(
                        destination_rect[y][0].x(),
                        destination_rect[y][0].y(),
                        destination_rect[y][0].x() + img.width(),
                        destination_rect[y][0].y()
                    )

            for x in range(1, len(self._balloon.clip_width)):
                painter.drawLine(
                    destination_rect[0][x].x(),
                    destination_rect[0][x].y(),
                    destination_rect[0][x].x(),
                    destination_rect[0][x].y() + img.height()
                )

            painter.setPen(Qt.green)
            painter.drawRect(QRect(0, 0, img.width() - 1, img.height() - 1))
            painter.drawText(3, 12, "DialogWindow")
            painter.drawText(3, 24, "ghost: %d" % self.id)
            painter.drawText(3, 36, "Name: %s" % self.name)
            painter.drawText(3, 48, "soul_id: %d" % soul_id)
        return img

    def get_menu_style(self):
        return self._menu_style

    def repaint(self):
        for soul in self._souls.values():
            soul.repaint()

    def get_shell_image(self):
        return self._shell_image

    # balloon ###################################################################################

    def set_balloon(self, name):
        self._balloon = self.get_balloon_by_name(name)
        if self._balloon is None:
            self._balloon = self.get_balloon(0)
            if self._balloon is None:
                raise ValueError("set_balloon: load defalut balloon fail.")

        self._balloon.load()

        for filename in self._balloon.image_list:
            p = os.path.join(self._balloon.root_path, filename)
            self._balloon_image[filename] = self._balloon.get_image(p)
        self._balloon_image_cache = self._balloon_image['background.png']

        for soul in self._souls.values():
            soul.set_balloon(self._balloon)

        self.memory_write('CurrentBalloonName', self._balloon.name)

    def get_current_balloon(self):
        return self._balloon

    def get_balloon(self, balloon_id):
        if 0 <= balloon_id < len(self._balloons):
            return self._balloons[balloon_id]

        logging.warning("get_balloon: index=%d NOT in shell list" % balloon_id)
        return None

    def get_balloon_by_name(self, balloon_name):
        if balloon_name in self._name2balloon_id:
            return self._balloons[self._name2balloon_id[balloon_name]]
        logging.warning("get_balloon_by_name: '%s' NOT in shell list" % balloon_name)
        return None

    def get_balloon_count(self):
        return len(self._balloons)

    # event #####################################################################################

    def on_update(self, update_time):
        is_need_update = False
        for soul in self._souls.values():
            if soul.on_update(update_time) is True:
                is_need_update = True

        if self._is_talking is False and self._now() - self._last_talk_time > self.get_auto_talk_interval():
            self.talk(self.get_auto_talk())
        self.exec_sakura_script(update_time)

        return is_need_update

    def memory_read(self, key, default, soul_id=0, table_name=None):
        if table_name is None:
            table_name = str('ghost_' + self.name)
        return kikka.memory.read(table_name, key, default, soul_id)

    def memory_write(self, key, value, soul_id=0, table_name=None):
        if table_name is None:
            table_name = str('ghost_' + self.name)
        kikka.memory.write(table_name, key, value, soul_id)

    def emit_ghost_event(self, param):
        self.signal.GhostEvent.emit(param)

    def ghost_event(self, param):
        is_talking = self.touch_talk(param)
        if not is_talking and param.event_type == GhostEvent.Shell_MouseDoubleClick:
            self.get_soul(param.soul_id).get_dialog().show(WindowDialog.DIALOG_MAIN_MENU)

    # talk #####################################################################################
    def get_auto_talk_interval(self):
        return 1000*60*10

    def get_variable(self, key):
        if key not in self._variables:
            logging.warning("getVariables: key[%s] not exist" % key)
            return None
        return self._variables[key]

    def set_variable(self, key, value):
        if key is None:
            return
        self._variables[key] = value

    def exec_sakura_script(self, update_time):
        if self._script_wait > 0:
            self._script_wait -= update_time
            return

        if self._is_talking is True and len(self._tokens) <= 0:
            self._is_talking = False
            self._last_talk_time = self._now()

            for soul in self._souls.values():
                soul.set_default_surface()
                soul.get_dialog().hide()
            return

        while len(self._tokens) > 0:
            token = self._tokens.pop(0)
            if token[0] == '':
                if len(token[1]) > 0:
                    self.on_talk(token[1][0])
                    if len(token[1]) > 1:
                        self._tokens.insert(0, ('', token[1][1:]))
                    self._script_wait = self._talk_speed
                    break
                else:
                    continue
            elif token[0] == '\\n':
                self.on_talk('\n')
            elif '\\0' == token[0]:
                self._current_talk_soul = 0
                continue
            elif '\\1' == token[0]:
                self._current_talk_soul = 1
                continue
            elif '\\w' in token[0]:
                t = token[0][2:]
                self._script_wait = int(t) * self._talk_speed
                break
            elif '\\_w' in token[0]:
                self._script_wait = int(token[1])
                break
            elif '\\s' == token[0]:
                self.get_soul(self._current_talk_soul).set_surface(int(token[1]))
                break
            elif '\\e' == token[0]:
                self._tokens = []
                self._script_wait = self._ending_wait
                break
            elif '%' == token[0][0]:
                command = token[0][1:]
                now = datetime.datetime.now()
                if command == 'month':
                    text = str(now.minute)
                elif command == 'day':
                    text = str(now.day)
                elif command == 'hour':
                    text = str(now.hour)
                elif command == 'hour12':
                    text = str(now.hour % 12)
                elif command == 'minute':
                    text = str(now.minute)
                elif command == 'second':
                    text = str(now.second)

                elif command == 'screenwidth':
                    w, h = kikka.helper.get_screen_resolution()
                    text = str(w)
                elif command == 'screenheight':
                    w, h = kikka.helper.get_screen_resolution()
                    text = str(h)

                elif command in self._variables:
                    text = self._variables[command]
                elif command == 'property':
                    text = str(kikka.core.get_property(token[1]))
                else:
                    text = ''
                    logging.warning('unknown sakura script command: %s %s' % (token[0], token[1]))
                if len(text) > 0:
                    self._tokens.insert(0, ('', text))
            else:
                logging.warning('unknown sakura script command: %s %s' % (token[0], token[1]))
        pass

    def talk(self, script):
        if script is None or script == '':
            return

        if kikka.core.get_state() in [kikka.core.APP_STATE.HIDE, kikka.core.APP_STATE.FULL_SCREEN]:
            return

        self.talk_clear()
        ss = SakuraScript(script)
        self._tokens = ss.tokens
        if len(self._tokens) <= 0:
            return
        if self._tokens[-1][0] != '\\e':
            self._tokens.append(('\\e', ''))

        self._last_talk_time = self._now()
        self._is_talking = True
        self._script_wait = 0

    def is_talking(self):
        return self._is_talking and kikka.core.get_state() == kikka.core.APP_STATE.SHOW

    def talk_clear(self):
        for soul in self._souls.values():
            soul.get_dialog().talk_clear()

    def _now(self):
        return time.clock() * 1000

    def get_auto_talk(self):
        return ''

    def touch_talk(self, param):
        return self.is_talking()

    def on_talk(self, message):
        dlg = self.get_soul(self._current_talk_soul).get_dialog()
        dlg.show(WindowDialog.DIALOG_TALK)
        dlg.on_talk(message, self._talk_speed)

    def on_boot(self):
        pass

    # control #####################################################################################

    def show(self):
        for soul in self._souls.values():
            soul.show()

    def hide(self):
        for soul in self._souls.values():
            soul.hide()

    def reset_windows_position(self, using_default_pos=True, lock_on_task_bar=False):
        right_offect = 0
        for soul in self._souls.values():
            soul.reset_windows_position(using_default_pos, lock_on_task_bar | self._is_lock_on_task_bar, right_offect)
            right_offect += soul.get_size().width()

    def set_is_lock_on_task_bar(self, is_lock):
        self._is_lock_on_task_bar = is_lock
        self.memory_write("isLockOnTaskBar", is_lock)
        self.reset_windows_position(False)

    def get_is_lock_on_task_bar(self):
        return self._is_lock_on_task_bar
