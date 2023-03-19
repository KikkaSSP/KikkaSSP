
import logging
import time
import random
from collections import OrderedDict

from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QActionGroup

import kikka
from kikka.const import WindowConst
from ghost.window_shell import WindowShell
from ghost.window_dialog import WindowDialog


class Soul:

    def __init__(self, ghost, soul_id, surface_id=0):
        self.id = soul_id
        self._ghost = ghost

        self._menu = None
        self._menu_style = None

        self._size = None
        self._window_shell = None
        self._window_dialogs = []

        self._clothes = {}
        self._surface = None
        self._animations = {}
        self._default_surface_id = surface_id

        self._draw_offset = []
        self._base_rect = QRect()
        self._base_image = None
        self._soul_image = None
        self._surface_image = None
        self._center_point = QPoint()

        self.init()

    def init(self):
        self._window_shell = WindowShell(self, self.id)
        self._size = self._window_shell.size()

        if self.id == 0:
            self._menu = kikka.menu.create_soul_main_menu(self._ghost)
        else:
            self._menu = kikka.menu.create_soul_default_menu(self._ghost)

        self.load_cloth_bind()
        current_shell = self._ghost.get_current_shell()
        shell_menu = self._menu.get_sub_menu("Shells")
        if shell_menu:
            shell_submenu = shell_menu.get_sub_menu(current_shell.catalog)
            if shell_submenu:
                shell_submenu.check_action(current_shell.unicode_name, True)

        self._window_dialogs.append(WindowDialog(self, 0))
        balloon = self._ghost.get_current_balloon()
        if balloon is not None:
            for dlg in self._window_dialogs:
                dlg.set_balloon(balloon)
            balloon_menu = self._menu.get_sub_menu("Balloons")
            if balloon_menu is not None:
                act = balloon_menu.get_action(balloon.name)
                act.setChecked(True)

        self.set_surface(self._default_surface_id)
        self.update_clothes_menu()
        kikka.menu.update_test_surface(self._menu, self._ghost, self._default_surface_id)

    def initialed(self):
        rect = self.memory_read('ShellRect', [])
        if rect:
            self._window_shell.move(rect[0], rect[1])
            self._window_shell.resize(rect[2], rect[3])
        else:
            soul = self._ghost.get_soul(self.id - 1)
            right_offset = soul.get_size().width() if soul else 0
            self.reset_windows_position(True, True, right_offset=right_offset)
        for dlg in self._window_dialogs:
            dlg.initialed()

    def show(self):
        self._window_shell.show()

    def hide(self):
        self._window_shell.hide()
        for dlg in self._window_dialogs:
            dlg.hide()

    def move(self, *__args):
        self._window_shell.move(*__args)

    def pos(self):
        return self._window_shell.pos()

    def show_menu(self, pos):
        if self._menu is not None:
            self._menu.set_position(pos)
            self._menu.show()
        pass

    def get_ghost(self):
        return self._ghost

    def get_window_shell(self):
        return self._window_shell

    def get_dialog(self, dialog_id=0):
        return self._window_dialogs[dialog_id]

    def set_balloon(self, balloon):
        for dlg in self._window_dialogs:
            dlg.set_balloon(balloon)
            dlg.repaint()

    def set_menu(self, Menu):
        self._menu = Menu

    def get_menu(self):
        return self._menu

    def update_clothes_menu(self):
        shell = self._ghost.get_current_shell()
        setting = shell.setting[self.id]
        clothes_menu = OrderedDict(sorted(setting.clothes_menu.items()))
        clothes_bind = shell.get_bind(self.id)
        bind_groups = setting.bind_groups
        bind_option = setting.bind_option

        menu = None
        for act in self._menu.actions():
            if act.text() == 'Clothes':
                menu = act.menu()
                break

        if menu is None:
            return

        menu.clear()
        self._clothes.clear()
        if len(clothes_menu) == 0:
            menu.setEnabled(False)
            return

        menu.setEnabled(True)

        group = {}
        for bind_group in bind_groups.values():
            if bind_group.type not in group:
                group[bind_group.type] = QActionGroup(menu.parent())
                if bind_group.type in bind_option:
                    option = bind_option[bind_group.type]
                    if option == 'multiple':
                        group[bind_group.type].setExclusive(False)
                    # logging.info("%s %s" % (bind_group.type, option))
        pass

        for aid in clothes_menu.values():
            if aid == -1:
                menu.addSeparator()
            elif aid in bind_groups.keys():
                bind_group = bind_groups[aid]
                text = "%s - %s" % (bind_group.type, bind_group.title)
                act = menu.add_menu_item(text, group=group[bind_group.type])

                def callback_func(checked, act=act, bind_group=bind_group):
                    self.click_clothes_menu_item(checked, act, bind_group)
                act.triggered.connect(callback_func)
                act.setCheckable(True)
                act.setData(aid)

                if bind_group.type not in self._clothes.keys():
                    self._clothes[bind_group.type] = -1

                if (len(clothes_bind) == 0 and bind_group.default is True) \
                        or (len(clothes_bind) > 0 and aid in clothes_bind):
                    self._clothes[bind_group.type] = bind_group.animation_id
                    act.setChecked(True)
                    self.set_clothes(bind_group.animation_id, True)
            pass
        pass

    def click_clothes_menu_item(self, checked, act, bind_group):
        shell = self._ghost.get_current_shell()
        setting = shell.setting[self.id]
        # bind_groups = setting.bind_groups
        bind_option = setting.bind_option

        # group = act.actionGroup()
        last_cloth = self._clothes[bind_group.type]
        if last_cloth == bind_group.animation_id:
            if (bind_group.type in bind_option and bind_option[bind_group.type] != 'mustselect') \
                    or bind_group.type not in bind_option:
                self._clothes[bind_group.type] = -1
                self.set_clothes(bind_group.animation_id, False)
                act.setChecked(not act.isChecked())
        else:
            self.set_clothes(last_cloth, False)
            self._clothes[bind_group.type] = bind_group.animation_id
            self.set_clothes(bind_group.animation_id, True)

        self.set_surface(-1)
        self.save_cloth_bind()
        logging.info("click_clothes_menu_item: %s %s", act.text(), act.isChecked())

    def save_cloth_bind(self):
        data = {}
        count = self.get_ghost().get_shell_count()
        for i in range(count):
            shell = self.get_ghost().get_shell(i)
            if len(shell.bind) > 0:
                data[shell.name] = shell.bind[self.id]
        self.memory_write('ClothBind', data)

    def load_cloth_bind(self):
        data = self.memory_read('ClothBind', {})
        if len(data) <= 0:
            return

        for name in data.keys():
            shell = self.get_ghost().get_shell_by_name(name)
            if shell is None:
                continue

            shell.bind[self.id] = data[name]
        pass

    def reset_animation(self, animations):
        self._animations.clear()
        for aid, ani in animations.items():
            self._animations[aid] = Animation(self, self.id, ani)
            self._animations[aid].update_draw_rect()

    def get_animation(self):
        return self._animations

    def get_running_animation(self):
        running_animation = []
        for aid, ani in self._animations.items():
            if ani.is_running is True:
                running_animation.append(aid)
        return running_animation

    def animation_start(self, aid):
        if aid in self._animations.keys():
            self._animations[aid].start()
        else:
            logging.warning("animation %d NOT exist!" % aid)

    def animation_stop(self, aid):
        if aid in self._animations.keys():
            self._animations[aid].stop()
        else:
            logging.warning("animation %d NOT exist!" % aid)

    def set_surface(self, surface_id=-1):
        if self._surface is None:
            surface_id = surface_id if surface_id != -1 else self._default_surface_id
        elif surface_id == -1:
            surface_id = self._surface.id
        elif surface_id == self._surface.id:
            return

        shell = self._ghost.get_current_shell()
        if surface_id in shell.alias.keys():
            surface_id = random.choice(shell.alias[surface_id])

        surface = shell.get_surface(surface_id)
        if surface is None and surface_id != self._default_surface_id:
            logging.info("get default surface %d", self._default_surface_id)
            surface = shell.get_surface(self._default_surface_id)
            surface_id = self._default_surface_id

        if surface is None:
            logging.error("setSurface FAIL")
            self._surface = None
            surface_id = -1
            self.reset_animation({})
        else:
            logging.info("setSurface: %3d - %s(%s)", surface.id, surface.name, surface.unicode_name)
            self._surface = surface
            self.reset_animation(surface.animations)
        self.update_draw_rect()
        self.repaint()
        self._window_shell.set_boxes(shell.get_collision_boxes(surface_id), self._draw_offset)
        kikka.menu.update_test_surface(self._menu, self._ghost, surface_id)

    def set_default_surface(self):
        self.set_surface(self._default_surface_id)

    def get_current_surface(self):
        return self._surface

    def get_current_surface_id(self):
        return self._surface.id if self._surface is not None else -1

    def set_clothes(self, aid, is_enable=True):
        self._ghost.get_current_shell().set_clothes(self.id, aid, is_enable)
        self.repaint()

    def get_size(self):
        return QSize(self._size)

    def get_draw_offset(self):
        return QPoint(self._draw_offset)

    def get_center_point(self):
        return QPoint(self._center_point)

    def get_base_rect(self):
        return QRect(self._base_rect)

    def reset_windows_position(self, using_default_pos=True, is_lock_task_bar=True, right_offset=0):
        shell = self._ghost.get_current_shell()

        w, h = kikka.helper.get_screen_client_rect()
        if using_default_pos is True:
            pos = QPoint(shell.setting[self.id].position)
            if pos.x() == WindowConst.UNSET.x():
                pos.setX(w - self._size.width() - right_offset)
        else:
            pos = self._window_shell.pos()

        if is_lock_task_bar is True or pos.y() == WindowConst.UNSET.y():
            pos.setY(h - self._size.height())

        self._window_shell.move(pos)
        self._window_shell.save_shell_rect()

    def memory_read(self, key, default):
        return self._ghost.memory_read(key, default, self.id)

    def memory_write(self, key, value):
        self._ghost.memory_write(key, value, self.id)

    # ################################################################

    def on_update(self, update_time):
        is_need_update = False
        for aid, ani in self._animations.items():
            if ani.on_update(update_time) is True:
                is_need_update = True

        if is_need_update is True:
            self.repaint()
        return is_need_update

    def repaint(self):
        self.repaint_base_image()
        self.repaint_soul_image()
        self._window_shell.set_image(self._soul_image)
        for dlg in self._window_dialogs:
            dlg.repaint()

    def get_shell_image(self, face_id):
        shell_image = self._ghost.get_shell_image()
        filename1 = "surface%04d.png" % face_id
        filename2 = "surface%d.png" % face_id
        if filename1 in shell_image:
            return shell_image[filename1]
        if filename2 in shell_image:
            return shell_image[filename2]
        else:
            logging.warning("Image lost: %s or %s" % (filename1, filename2))
            return kikka.helper.get_default_image()

    def update_draw_rect(self):
        if self._surface is None or self._surface.id == -1:
            self._draw_offset = self._ghost.get_current_shell().get_offset(self.id)
            self._size = kikka.const.WindowConst.ShellWindowDefaultSize
            self._center_point = kikka.const.WindowConst.ShellWindowDefaultCenter
            self._base_rect = QRect(self._draw_offset, self._size)
        else:
            shell_image = self._ghost.get_shell_image()
            base_rect = QRect()
            if len(self._surface.elements) > 0:
                for i, ele in self._surface.elements.items():
                    if ele.filename in shell_image:
                        base_rect = base_rect.united(QRect(ele.offset, shell_image[ele.filename].size()))
            else:
                img = self.get_shell_image(self._surface.id)
                base_rect = QRect(0, 0, img.width(), img.height())

            self._base_rect = QRect(base_rect)
            base_rect.translate(self._ghost.get_current_shell().get_offset(self.id))
            rect = QRect(base_rect)
            for aid, ani in self._animations.items():
                rect = rect.united(ani.rect)

            self._draw_offset = QPoint(base_rect.x() - rect.x(), base_rect.y() - rect.y())
            self._size = rect.size()

            if self._surface.base_pos != WindowConst.UNSET:
                self._center_point = self._surface.base_pos
            else:
                self._center_point = QPoint(self._size.width() / 2, self._size.height())
        pass

    def repaint_base_image(self):
        shell_image = self._ghost.get_shell_image()

        self._base_image = QImage(self._size, QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(self._base_image)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self._base_image.rect(), Qt.transparent)
        painter.end()
        del painter

        if self._surface is None:
            return

        if len(self._surface.elements) > 0:
            for i, ele in self._surface.elements.items():
                if ele.filename in shell_image:
                    offset = self._draw_offset + ele.offset
                    kikka.helper.draw_image(
                        self._base_image, shell_image[ele.filename],
                        offset.x(),
                        offset.y(),
                        ele.paint_type
                    )
        else:
            img = self.get_shell_image(self._surface.id)
            painter = QPainter(self._base_image)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(self._draw_offset, img)
            painter.end()
        # self._base_image.save("_base_image.png")
        pass

    def repaint_soul_image(self):
        self._soul_image = QImage(self._base_image)
        for aid, ani in self._animations.items():
            ani.draw(self._soul_image)
        pass


class Animation:
    def __init__(self, soul, win_id, animation_data):
        self._soul = soul
        self._ghost = soul.get_ghost()
        self._win_id = win_id
        self.id = animation_data.id
        self.data = animation_data
        self.patterns = animation_data.patterns
        self.interval = animation_data.interval
        self.interval_value = animation_data.interval_value
        self.exclusive = animation_data.exclusive

        self.is_running = False
        self.is_finish = True
        self._update_time = 0
        self._current_pattern = -1
        self._last_time = 0

        self._image = None
        self._draw_offset = QPoint()
        self._draw_type = None
        self.rect = QRect()

        if self.interval == 'runonce':
            self.start()

    def update_draw_rect(self):
        self.rect = QRect()
        for pid, p in self.patterns.items():
            if p.is_control_pattern() is False and p.surface_id != -1:
                img = self._soul.get_shell_image(p.surface_id)
                self.rect = self.rect.united(QRect(p.offset, img.size()))
        pass

    def start(self):
        if self.is_running is False or self.is_finish is True:
            logging.debug("Animation %d start" % self.id)

            self.is_running = True
            self.is_finish = False
            self._update_time = 0
            self._current_pattern = -1

    def stop(self):
        self.is_running = False
        self.is_finish = True
        self._current_pattern = -1
        self._image = None

    def random_start(self, update_time):
        if self.is_finish is False:
            return False

        isNeedStart = False
        if self.interval == 'never' \
                or self.interval == 'talk' \
                or self.interval == 'bind' \
                or self.interval == 'yen-e' \
                or self.interval == 'runonce':
            isNeedStart = False

        elif self.interval == 'sometimes':
            # 20% per second
            isNeedStart = True if random.random() < 0.0002 * update_time else False

        elif self.interval == 'rarely':
            # 10% per second
            isNeedStart = True if random.random() < 0.0001 * update_time else False

        elif self.interval == 'random':
            # n% per second
            isNeedStart = True if random.random() < self.interval_value / 100000 * update_time else False

        elif self.interval == 'periodic':
            now = time.clock()
            if now - self._last_time >= self.interval_value:
                self._last_time = now
                isNeedStart = True
            else:
                isNeedStart = False

        elif self.interval == 'always':
            isNeedStart = True

        return isNeedStart

    def do_pattern(self, pattern):
        logging.debug("aid:%d %s doPattern %d %s", self.id, self.interval, pattern.id, pattern.method_type)

        if pattern.method_type in ['alternativestart', 'start', 'insert']:
            r = random.choice(self.patterns[0].aid)
            self._soul.animation_start(r)
            pattern.bind_animation = r
        elif pattern.method_type in ['alternativestop', 'stop']:
            for aid in self.patterns[0].aid:
                self._soul.animation_stop(aid)
                pattern.bind_animation = -1
        else:
            self._image = self._soul.get_shell_image(pattern.surface_id)
            self._draw_offset = pattern.offset
            self._draw_type = pattern.method_type
        pass

    def is_all_bind_animation_finish(self):
        has_control_pattern = False
        all_stop = True
        animations = self._soul.get_animation()
        for pid, pattern in self.patterns.items():
            if pattern.is_control_pattern() and pattern.bind_animation != -1:
                has_control_pattern = True
                if animations[pattern.bind_animation].is_finish is False:
                    all_stop = False
                    break
                else:
                    pattern.bind_animation = -1

        return True if has_control_pattern is True and all_stop is True else False

    def on_update(self, update_time):
        is_need_update = False
        if self.random_start(update_time) is True:
            self.start()
            is_need_update = True

        if self.is_running is False:
            return is_need_update

        self._update_time += update_time
        while self._current_pattern + 1 < len(self.patterns) \
                and self._update_time > self.patterns[self._current_pattern + 1].time:
            is_need_update = True
            self._current_pattern += 1
            pattern = self.patterns[self._current_pattern]

            if pattern.surface_id == -1:
                self._update_time = 0
                self.stop()
                break

            self._update_time -= pattern.time
            self.do_pattern(pattern)

        if self._current_pattern + 1 >= len(self.patterns):
            self.is_finish = True

        if self.is_all_bind_animation_finish() is True:
            self._update_time = 0
            self.stop()

        return is_need_update

    def draw(self, dest_image):
        if self.id in self._soul.get_ghost().get_current_shell().get_bind(self._soul.id):
            for p in self.patterns.values():
                self.do_pattern(p)
                offset = self._soul.get_draw_offset() + self._draw_offset
                kikka.helper.draw_image(dest_image, self._image, offset.x(), offset.y(), self._draw_type)
        else:
            offset = self._soul.get_draw_offset() + self._draw_offset
            kikka.helper.draw_image(dest_image, self._image, offset.x(), offset.y(), self._draw_type)

        return dest_image
