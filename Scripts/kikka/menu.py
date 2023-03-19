# coding=utf-8
import logging
import os

from PyQt5.QtCore import QRect, QSize, Qt, QRectF, QPoint, QEvent
from PyQt5.QtWidgets import QMenu, QStyle, QStyleOptionMenuItem, QStyleOption, QWidget, QApplication, QActionGroup
from PyQt5.QtWidgets import QAction, QToolTip
from PyQt5.QtGui import QIcon, QPainter, QFont, QPalette, QColor, QKeySequence

import kikka
from kikka.helper import Singleton


class KikkaMenu(Singleton):
    isDebug = False

    def __init__(self):
        pass

    @staticmethod
    def get_menu(ghost_id, soul_id):
        ghost = kikka.core.get_ghost(ghost_id)
        if ghost is not None:
            return ghost.get_soul(soul_id).get_menu()
        else:
            logging.warning('menu lost')
            return None

    @staticmethod
    def set_app_menu(menu):
        QApplication.instance().trayIcon.setContextMenu(None)
        QApplication.instance().trayIcon.setContextMenu(menu)

    @staticmethod
    def create_soul_main_menu(ghost):
        import kikka

        parent = QWidget(flags=Qt.Dialog)
        main_menu = Menu(parent, ghost.id, "Main")

        # shell list
        menu = Menu(main_menu, ghost.id, "Shells")
        group1 = QActionGroup(parent)
        catalog = {"Normal": Menu(menu, ghost.id, "Normal")}
        for i in range(ghost.get_shell_count()):
            shell = ghost.get_shell(i)
            if shell.catalog not in catalog:
                catalog[shell.catalog] = Menu(menu, ghost.id, shell.catalog)

            def callback_func(checked, name=shell.name): ghost.change_shell(name)
            act = catalog[shell.catalog].add_menu_item(shell.unicode_name, callback_func, None, group1)
            act.setData(shell.name)
            act.setCheckable(True)
            act.setToolTip(shell.description)

        for k, m in catalog.items():
            m.setToolTipsVisible(True)
            menu.add_sub_menu(m)
        main_menu.add_sub_menu(menu)

        # clothes list
        menu = Menu(main_menu, ghost.id, "Clothes")
        menu.setEnabled(False)
        main_menu.add_sub_menu(menu)

        # balloon list
        menu = Menu(main_menu, ghost.id, "Balloons")
        group2 = QActionGroup(parent)
        for i in range(ghost.get_balloon_count()):
            balloon = ghost.get_balloon(i)
            def callbackfunc(checked, name=balloon.name): ghost.set_balloon(name)
            act = menu.add_menu_item(balloon.unicode_name, callbackfunc, None, group2)
            act.setCheckable(True)
        main_menu.add_sub_menu(menu)

        option_menu = KikkaMenu.create_option_menu(parent, ghost)
        main_menu.add_sub_menu(option_menu)

        # debug option
        if kikka.core.isDebug is True:

            def callback_function1():
                kikka.core.isDebug = not kikka.core.isDebug
                kikka.core.repaint_all_ghost()

            def callback_function2():
                kikka.ghost.isDebug = not kikka.ghost.isDebug
                kikka.core.repaint_all_ghost()

            menu = Menu(main_menu, ghost.id, "Debug")

            act = menu.add_menu_item("Show ghost data", callback_function1)
            act.setCheckable(True)
            act.setChecked(kikka.core.isDebug is True)

            act = menu.add_menu_item("Show shell frame", callback_function2)
            act.setCheckable(True)
            act.setChecked(kikka.ghost.isDebug is True)

            menu.add_sub_menu(Menu(menu, ghost.id, "TestSurface"))
            menu.add_sub_menu(KikkaMenu.create_test_menu(menu))

            main_menu.addSeparator()
            main_menu.add_sub_menu(menu)
        pass

        main_menu.addSeparator()
        main_menu.add_menu_item("Exit", lambda: kikka.app.exit_app())
        return main_menu

    @staticmethod
    def create_soul_default_menu(ghost):
        import kikka

        parent = QWidget(flags=Qt.Dialog)
        main_menu = Menu(parent, ghost.id, "Main")

        # shell list
        menu = Menu(main_menu, ghost.id, "Shells")
        group1 = QActionGroup(parent)
        for i in range(ghost.get_shell_count()):
            shell = ghost.get_shell(i)

            def callback_func(checked, name=shell.name): ghost.change_shell(name)
            act = menu.add_menu_item(shell.unicode_name, callback_func, None, group1)
            act.setData(shell.name)
            act.setCheckable(True)
        main_menu.add_sub_menu(menu)

        # clothes list
        menu = Menu(main_menu, ghost.id, "Clothes")
        menu.setEnabled(False)
        main_menu.add_sub_menu(menu)

        main_menu.add_menu_item("Exit", lambda: kikka.app.exit_app())

        return main_menu

    @staticmethod
    def create_option_menu(parent, ghost):
        option_menu = Menu(parent, ghost.id, "Option")

        option_menu.add_menu_item("Reset Shell Position", lambda checked: ghost.reset_windows_position(True, False))

        act = option_menu.add_menu_item("Lock on task bar", lambda checked, g=ghost: g.set_is_lock_on_task_bar(checked))
        act.setCheckable(True)
        act.setChecked(ghost.get_is_lock_on_task_bar())

        return option_menu

    # ###########################################################################
    @staticmethod
    def create_test_menu(parent=None):
        # test callback function
        def _test_callback(index=0, title=''):
            logging.info("MainMenu_callback: click [%d] %s" % (index, title))

        def _test_exit(test_menu):
            test_menu.add_menu_item("Exit", lambda: kikka.app.exit_app())

        def _test_menu_item_state(test_menu):
            menu = Menu(test_menu, 0, "MenuItem State")
            c = 16
            for i in range(c):
                text = str("%s-item%d" % (menu.title(), i))
                act = menu.add_menu_item(text, lambda checked, a=i, b=text: _test_callback(a, b))

                if i >= c / 2:
                    act.setDisabled(True)
                    act.setText("%s-disable" % act.text())
                if i % 8 >= c / 4:
                    act.setIcon(icon)
                    act.setText("%s-icon" % act.text())
                if i % 4 >= c / 8:
                    act.setCheckable(True)
                    act.setText("%s-ckeckable" % act.text())
                if i % 2 >= c / 16:
                    act.setChecked(True)
                    act.setText("%s-checked" % act.text())
            test_menu.add_sub_menu(menu)

        def _test_shortcut(test_menu):
            menu = Menu(test_menu, 0, "Shortcut")

            c = 4
            for i in range(c):
                text = str("%s-item" % (str(chr(ord('A') + i))))
                act = menu.add_menu_item(text, lambda checked, a=i, b=text: _test_callback(a, b))

                if i == 0:
                    act.setShortcut(QKeySequence("Ctrl+T"))
                    act.setShortcutContext(Qt.ApplicationShortcut)
                    act.setShortcutVisibleInContextMenu(True)
            test_menu.add_sub_menu(menu)

        def _test_status_tip(test_menu):
            pass

        def _test_separator(test_menu):
            menu = Menu(test_menu, 0, "Separator")
            menu.addSeparator()
            c = 5
            for i in range(c):
                text = str("%s-item%d" % (menu.title(), i))
                menu.add_menu_item(text, lambda checked, a=i, b=text: _test_callback(a, b))
                for j in range(i + 2):
                    menu.addSeparator()
            test_menu.add_sub_menu(menu)

        def _test_multiple_item(test_menu):
            menu = Menu(test_menu, 0, "Multiple item")
            for i in range(100):
                text = str("%s-item%d" % (menu.title(), i))
                menu.add_menu_item(text, lambda checked, a=i, b=text: _test_callback(a, b))
            test_menu.add_sub_menu(menu)

        def _test_long_text_item(test_menu):
            menu = Menu(test_menu, 0, "Long text item")
            for i in range(5):
                text = str("%s-item%d " % (menu.title(), i)) * 20
                menu.add_menu_item(text, lambda checked, a=i, b=text: _test_callback(a, b))
            test_menu.add_sub_menu(menu)

        def _test_large_menu(test_menu):
            menu = Menu(test_menu, 0, "Large menu")
            for i in range(60):
                text = str("%s-item%d " % (menu.title(), i)) * 10
                menu.add_menu_item(text, lambda checked, a=i, b=text: _test_callback(a, b))
                if i % 5 == 0:
                    menu.addSeparator()
            test_menu.add_sub_menu(menu)

        def _test_limit_test(test_menu):
            menu = Menu(test_menu, 0, "LimitTest")
            _test_large_menu(menu)
            _test_multiple_item(menu)
            _test_long_text_item(menu)
            test_menu.add_sub_menu(menu)

        def _test_submenu(test_menu):
            menu = Menu(test_menu, 0, "Submenu")
            test_menu.add_sub_menu(menu)

            submenu = Menu(menu, 0, "submenu1")
            menu.add_sub_menu(submenu)
            m = submenu
            for i in range(8):
                next = Menu(test_menu, 0, "submenu%d" % (i + 2))
                m.add_sub_menu(next)
                m = next

            submenu = Menu(menu, 0, "submenu2")
            menu.add_sub_menu(submenu)
            m = submenu
            for i in range(8):
                for j in range(10):
                    text = str("%s-item%d" % (m.title(), j))
                    m.add_menu_item(text, lambda checked, a=j, b=text: _test_callback(a, b))
                next = Menu(test_menu, 0, "submenu%d" % (i + 2))
                m.add_sub_menu(next)
                m = next

            submenu = Menu(test_menu, 0, "SubMenu State")
            c = 16
            for i in range(c):
                text = str("%s-%d" % (submenu.title(), i))
                m = Menu(submenu, 0, text)
                act = submenu.add_sub_menu(m)
                act.triggered.connect(lambda checked, a=i, b=text: _test_callback(a, b))
                if i >= c / 2:
                    act.setDisabled(True)
                    act.setText("%s-disable" % act.text())
                if i % 8 >= c / 4:
                    act.setIcon(icon)
                    act.setText("%s-icon" % act.text())
                if i % 4 >= c / 8:
                    act.setCheckable(True)
                    act.setText("%s-ckeckable" % act.text())
                if i % 2 >= c / 16:
                    act.setChecked(True)
                    act.setText("%s-checked" % act.text())
                submenu.add_sub_menu(m)
            menu.add_sub_menu(submenu)

        def _test_image_test(test_menu):
            image_test_menu = Menu(test_menu, 0, "ImageTest")
            test_menu.add_sub_menu(image_test_menu)

            menu = Menu(image_test_menu, 0, "MenuImage-normal")
            for i in range(32):
                text = " " * 54
                menu.add_menu_item(text)
            image_test_menu.add_sub_menu(menu)

            menu = Menu(image_test_menu, 0, "MenuImage-bit")
            menu.add_menu_item('')
            image_test_menu.add_sub_menu(menu)

            menu = Menu(image_test_menu, 0, "MenuImage-small")
            for i in range(10):
                text = " " * 30
                menu.add_menu_item(text)
            image_test_menu.add_sub_menu(menu)

            menu = Menu(image_test_menu, 0, "MenuImage-long")
            for i in range(64):
                text = " " * 54
                menu.add_menu_item(text)
            image_test_menu.add_sub_menu(menu)

            menu = Menu(image_test_menu, 0, "MenuImage-long2")
            for i in range(32):
                text = " " * 30
                menu.add_menu_item(text)
            image_test_menu.add_sub_menu(menu)

            menu = Menu(image_test_menu, 0, "MenuImage-large")
            for i in range(64):
                text = " " * 300
                menu.add_menu_item(text)
            image_test_menu.add_sub_menu(menu)

            menu = Menu(image_test_menu, 0, "MenuImage-verylarge")
            for i in range(100):
                text = " " * 600
                menu.add_menu_item(text)
            image_test_menu.add_sub_menu(menu)

        if parent is None:
            parent = QWidget(flags=Qt.Dialog)
        icon = QIcon(r"icon.ico")
        menu_test = Menu(parent, 0, "test_menu")

        _test_exit(menu_test)
        menu_test.addSeparator()
        _test_menu_item_state(menu_test)
        _test_shortcut(menu_test)
        _test_status_tip(menu_test)
        _test_separator(menu_test)
        _test_limit_test(menu_test)
        _test_submenu(menu_test)
        menu_test.addSeparator()
        _test_image_test(menu_test)
        menu_test.addSeparator()
        _test_exit(menu_test)

        return menu_test

    @staticmethod
    def update_test_surface(menu, ghost, cur_surface=-1):
        if kikka.core.isDebug is False or menu is None:
            return

        debug_menu = None
        for act in menu.actions():
            if act.text() == 'Debug':
                debug_menu = act.menu()
                break

        if debug_menu is None:
            return

        suface_menu = None
        for act in debug_menu.actions():
            if act.text() == 'TestSurface':
                suface_menu = act.menu()
                break

        if suface_menu is None:
            return

        suface_menu.clear()
        surface_list = ghost.get_current_shell().get_surface_name_list()
        group = QActionGroup(suface_menu.parent())
        for surface_id, item in surface_list.items():

            def callback_func(checked, faceID=surface_id): ghost.get_soul(0).set_surface(faceID)
            name = "%3d - %s(%s)" % (surface_id, item[0], item[1])
            act = suface_menu.add_menu_item(name, callback_func, None, group)
            act.setCheckable(True)
            if surface_id == cur_surface:
                act.setChecked(True)
        pass


class MenuStyle:
    def __init__(self, shell_menu, image_list):
        # image
        if shell_menu.bg_image in image_list:
            self.bg_image = image_list[shell_menu.bg_image]
        else:
            self.bg_image = kikka.helper.get_default_image()
            logging.warning("Menu background image NOT found: %s" % shell_menu.bg_image)

        if shell_menu.fg_image in image_list:
            self.fg_image = image_list[shell_menu.fg_image]
        else:
            self.fg_image = kikka.helper.get_default_image()
            logging.warning("Menu foreground image NOT found: %s" % shell_menu.fg_image)

        if shell_menu.sidebar_image in image_list:
            self.side_image = image_list[shell_menu.sidebar_image]
        else:
            self.side_image = kikka.helper.get_default_image()
            logging.warning("Menu sidebar image NOT found: %s" % shell_menu.sidebar_image)

        # font and color
        if shell_menu.font_family != '':
            self.font = QFont(shell_menu.font_family, shell_menu.font_size)
        else:
            self.font = None

        def get_color(color_list):
            return QColor(color_list[0], color_list[1], color_list[2]) if -1 not in color_list else None

        self.bg_font_color = get_color(shell_menu.bg_font_color)
        self.fg_font_color = get_color(shell_menu.fg_font_color)
        self.disable_font_color = get_color(shell_menu.disable_font_color)
        self.separator_color = get_color(shell_menu.separator_color)

        # others
        self.hidden = shell_menu.hidden
        self.background_alignment = shell_menu.background_alignment
        self.foreground_alignment = shell_menu.foreground_alignment
        self.sidebar_alignment = shell_menu.sidebar_alignment

    def get_pen_color(self, opt):
        if opt.menuItemType == QStyleOptionMenuItem.Separator:
            color = self.separator_color
        elif opt.state & QStyle.State_Selected and opt.state & QStyle.State_Enabled:
            color = self.fg_font_color
        elif not (int(opt.state) & int(QStyle.State_Enabled)):
            color = self.disable_font_color
        else:
            color = self.bg_font_color

        if color is None:
            color = opt.palette.color(QPalette.Text)
        return color


class Menu(QMenu):
    def __init__(self, parent, gid, title=''):
        QMenu.__init__(self, title, parent)

        self.gid = gid
        self._parent = parent
        self._action_rect = {}
        self._bg_image = None
        self._fg_image = None
        self._side_image = None
        self._actions = {}
        self._menus = {}

        self.installEventFilter(self)
        self.setMouseTracking(True)
        self.setStyleSheet("QMenu { menu-scrollable: 1; }")
        self.setSeparatorsCollapsible(False)

    def add_menu_item(self, text, callback_func=None, icon_file_path=None, group=None):
        if icon_file_path is None:
            act = QAction(text, self._parent)
        elif os.path.exists(icon_file_path):
            act = QAction(QIcon(icon_file_path), text, self._parent)
        else:
            logging.info("fail to add menu item")
            return

        if callback_func is not None:
            act.triggered.connect(callback_func)

        if group is None:
            self.addAction(act)
        else:
            self.addAction(group.addAction(act))
        self._actions[text] = act

        self.confirm_menu_size(act)
        return act

    def add_sub_menu(self, menu):
        act = self.addMenu(menu)
        self.confirm_menu_size(act, menu.title())
        self._actions[menu.title()] = act
        self._menus[menu.title()] = act.menu()
        return act

    def get_sub_menu(self, menu_name):
        return self._menus[menu_name] if menu_name in self._menus else None

    def get_action(self, action_name):
        return self._actions[action_name] if action_name in self._actions else None

    def get_action_by_data(self, data):
        for i in range(len(self.actions())):
            act = self.actions()[i]
            if act.data() == data:
                return act
        return None

    def check_action(self, action_name, is_checked):
        for i in range(len(self.actions())):
            act = self.actions()[i]
            if act.text() != action_name:
                continue

            act.setChecked(is_checked)
        pass

    def confirm_menu_size(self, item, text=''):
        s = self.sizeHint()
        w, h = kikka.helper.get_screen_resolution()

        if text == '':
            text = item.text()
        if KikkaMenu.isDebug and s.height() > h:
            logging.warning("the Menu_Height out of Screen_Height, too many menu item when add: %s" % text)
        if KikkaMenu.isDebug and s.width() > w:
            logging.warning("the Menu_Width out of Screen_Width, too menu item text too long when add: %s" % text)

    def set_position(self, pos):
        w, h = kikka.helper.get_screen_resolution()
        if pos.y() + self.height() > h:
            pos.setY(h - self.height())
        if pos.y() < 0:
            pos.setY(0)

        if pos.x() + self.width() > w:
            pos.setX(w - self.width())
        if pos.x() < 0:
            pos.setX(0)
        self.move(pos)

    def update_action_rect(self):
        """
        void QMenuPrivate::updateActionRects(const QRect &screen) const
        https://cep.xray.aps.anl.gov/software/qt4-x11-4.8.6-browser/da/d61/class_q_menu_private.html#acf93cda3ebe88b1234dc519c5f1b0f5d
        """
        self._action_rect = {}
        top_margin = 0
        left_margin = 0
        right_margin = 0

        # qmenu.cpp Line 259:
        # init
        max_column_width = 0
        dh = self.height()
        y = 0
        style = self.style()
        opt = QStyleOption()
        opt.initFrom(self)
        h_margin = style.pixelMetric(QStyle.PM_MenuHMargin, opt, self)
        v_margin = style.pixelMetric(QStyle.PM_MenuVMargin, opt, self)
        icon_ = style.pixelMetric(QStyle.PM_SmallIconSize, opt, self)
        fw = style.pixelMetric(QStyle.PM_MenuPanelWidth, opt, self)
        desk_frame_width = style.pixelMetric(QStyle.PM_MenuDesktopFrameWidth, opt, self)
        tear_off_height = style.pixelMetric(QStyle.PM_MenuTearoffHeight, opt, self) if self.isTearOffEnabled() else 0

        # for compatibility now - will have to refactor this away
        tab_width = 0
        max_icon_width = 0
        has_checkable_items = False
        # ncols = 1
        # sloppyAction = 0

        for i in range(len(self.actions())):
            act = self.actions()[i]
            if act.isSeparator() or act.isVisible() is False:
                continue
            # ..and some members
            has_checkable_items |= act.isCheckable()
            ic = act.icon()
            if ic.isNull() is False:
                max_icon_width = max(max_icon_width, icon_ + 4)

        # qmenu.cpp Line 291:
        # calculate size
        qfm = self.fontMetrics()
        previous_was_separator = True  # this is true to allow removing the leading separators
        for i in range(len(self.actions())):
            act = self.actions()[i]

            if not act.isVisible() or (self.separatorsCollapsible() and previous_was_separator and act.isSeparator()):
                # we continue, this action will get an empty QRect
                self._action_rect[i] = QRect()
                continue

            previous_was_separator = act.isSeparator()

            # let the style modify the above size..
            opt = QStyleOptionMenuItem()
            self.initStyleOption(opt, act)
            fm = opt.fontMetrics

            sz = QSize()
            # sz = self.sizeHint().expandedTo(self.minimumSize())
            # sz = sz.expandedTo(self.minimumSizeHint()).boundedTo(self.maximumSize())

            # calc what I think the size is..
            if act.isSeparator():
                sz = QSize(2, 2)
            else:
                s = act.text()
                if '\t' in s:
                    t = s.index('\t')
                    act.setText(s[t + 1:])
                    tab_width = max(int(tab_width), qfm.width(s[t + 1:]))
                else:
                    seq = act.shortcut()
                    if seq.isEmpty() is False:
                        tab_width = max(int(tab_width), qfm.width(seq.toString()))

                sz.setWidth(fm.boundingRect(QRect(), Qt.TextSingleLine | Qt.TextShowMnemonic, s).width())
                sz.setHeight(fm.height())

                if not act.icon().isNull():
                    is_sz = QSize(icon_, icon_)
                    if is_sz.height() > sz.height():
                        sz.setHeight(is_sz.height())

            sz = style.sizeFromContents(QStyle.CT_MenuItem, opt, sz, self)

            if sz.isEmpty() is False:
                max_column_width = max(max_column_width, sz.width())
                # wrapping
                if y + sz.height() + v_margin > dh - desk_frame_width * 2:
                    # ncols += 1
                    y = v_margin
                y += sz.height()
                # update the item
                self._action_rect[i] = QRect(0, 0, sz.width(), sz.height())
        pass  # exit for

        max_column_width += tab_width  # finally add in the tab width
        content_size = style.sizeFromContents(QStyle.CT_Menu, opt, QApplication.globalStrut(), self)
        sfc_margin = content_size.width() - QApplication.globalStrut().width()
        min_column_width = self.minimumWidth() - (sfc_margin + left_margin + right_margin + 2 * (fw + h_margin))
        max_column_width = max(min_column_width, max_column_width)

        # qmenu.cpp Line 259:
        # calculate position
        base_y = v_margin + fw + top_margin + tear_off_height
        x = h_margin + fw + left_margin
        y = base_y

        for i in range(len(self.actions())):
            if self._action_rect[i].isNull():
                continue
            if y + self._action_rect[i].height() > dh - desk_frame_width * 2:
                x += max_column_width + h_margin
                y = base_y

            self._action_rect[i].translate(x, y)  # move
            self._action_rect[i].setWidth(max_column_width)  # uniform width
            y += self._action_rect[i].height()

        # update menu size
        s = self.sizeHint()
        self.resize(s)

    def draw_control(self, p, opt, action_rect, icon, menu_style):
        """
        due to overrides the "paintEvent" method, so we must repaint all menu item by self.
        luckly, we have qt source code to reference.

        void drawControl (ControlElement element, const QStyleOption *opt, QPainter *p, const QWidget *w=0) const
        https://cep.xray.aps.anl.gov/software/qt4-x11-4.8.6-browser/df/d91/class_q_style_sheet_style.html#ab92c0e0406eae9a15bc126b67f88c110
        Line 3533: element = CE_MenuItem
        """

        style = self.style()
        p.setPen(menu_style.get_pen_color(opt))

        # Line 3566: draw icon and checked sign
        checkable = opt.checkType != QStyleOptionMenuItem.NotCheckable
        checked = opt.checked if checkable else False
        if opt.icon.isNull() is False:  # has custom icon
            dis = not (int(opt.state) & int(QStyle.State_Enabled))
            active = int(opt.state) & int(QStyle.State_Selected)
            mode = QIcon.Disabled if dis else QIcon.Normal
            if active != 0 and not dis:
                mode = QIcon.Active

            fw = style.pixelMetric(QStyle.PM_MenuPanelWidth, opt, self)
            icon_ = style.pixelMetric(QStyle.PM_SmallIconSize, opt, self)
            icon_rect = QRectF(action_rect.x() - fw, action_rect.y(), self._side_image.width(), action_rect.height())
            if checked:
                pix_map = icon.pixmap(QSize(icon_, icon_), mode, QIcon.On)
            else:
                pix_map = icon.pixmap(QSize(icon_, icon_), mode)

            pix_w = pix_map.width()
            pix_h = pix_map.height()
            pmr = QRectF(0, 0, pix_w, pix_h)
            pmr.moveCenter(icon_rect.center())

            if checked:
                p.drawRect(QRectF(pmr.x() - 1, pmr.y() - 1, pix_w + 2, pix_h + 2))
            p.drawPixmap(pmr.topLeft(), pix_map)

        elif checkable and checked:  # draw default checked sign
            opt.rect = QRect(0, action_rect.y(), self._side_image.width(), action_rect.height())
            opt.palette.setColor(QPalette.Text, menu_style.get_pen_color(opt))
            style.drawPrimitive(QStyle.PE_IndicatorMenuCheckMark, opt, p, self)

        # Line 3604: draw emnu text
        font = menu_style.font
        if font is not None:
            p.setFont(font)
        else:
            p.setFont(opt.font)
        text_flag = Qt.AlignVCenter | Qt.TextShowMnemonic | Qt.TextDontClip | Qt.TextSingleLine

        tr = QRect(action_rect)
        s = opt.text
        if '\t' in s:
            ss = s[s.index('\t') + 1:]
            font_width = opt.fontMetrics.width(ss)
            tr.moveLeft(opt.rect.right() - font_width)
            tr = QStyle.visualRect(opt.direction, opt.rect, tr)
            p.drawText(tr, text_flag, ss)
        tr.moveLeft(self._side_image.width() + action_rect.x())
        tr = QStyle.visualRect(opt.direction, opt.rect, tr)
        p.drawText(tr, text_flag, s)

        # Line 3622: draw sub menu arrow
        if opt.menuItemType == QStyleOptionMenuItem.SubMenu:
            arrow_w = style.pixelMetric(QStyle.PM_IndicatorWidth, opt, self)
            arrow_h = style.pixelMetric(QStyle.PM_IndicatorHeight, opt, self)
            arrow_rect = QRect(0, 0, arrow_w, arrow_h)
            arrow_rect.moveBottomRight(action_rect.bottomRight())
            arrow = QStyle.PE_IndicatorArrowLeft if opt.direction == Qt.RightToLeft else QStyle.PE_IndicatorArrowRight

            opt.rect = arrow_rect
            opt.palette.setColor(QPalette.ButtonText, menu_style.get_pen_color(opt))
            style.drawPrimitive(arrow, opt, p, self)
        pass

    def paintEvent(self, event):
        # init
        menu_style = kikka.core.get_ghost(self.gid).get_menu_style()
        self._bg_image = menu_style.bg_image
        self._fg_image = menu_style.fg_image
        self._side_image = menu_style.side_image
        self.update_action_rect()
        p = QPainter(self)

        # draw background
        p.fillRect(QRect(QPoint(), self.size()), self._side_image.pixelColor(0, 0))
        vertical = False
        y = self.height()
        while y > 0:
            yy = y - self._bg_image.height()
            p.drawImage(0, yy, self._side_image.mirrored(False, vertical))
            x = self._side_image.width()
            while x < self.width():
                p.drawImage(x, yy, self._bg_image.mirrored(False, vertical))
                x += self._bg_image.width()
                p.drawImage(x, yy, self._bg_image.mirrored(True, vertical))
                x += self._bg_image.width() + 1
            y -= self._bg_image.height()
            vertical = not vertical

        # draw item
        action_count = len(self.actions())
        for i in range(action_count):
            act = self.actions()[i]
            act_rect = QRect(self._action_rect[i])
            if event.rect().intersects(act_rect) is False:
                continue

            opt = QStyleOptionMenuItem()
            self.initStyleOption(opt, act)
            opt.rect = act_rect
            if opt.state & QStyle.State_Selected \
                    and opt.state & QStyle.State_Enabled:
                # Selected Item, draw foreground image
                p.setClipping(True)
                p.setClipRect(act_rect.x() + self._side_image.width(),
                              act_rect.y(),
                              self.width() - self._side_image.width(),
                              act_rect.height())

                p.fillRect(QRect(QPoint(), self.size()), self._fg_image.pixelColor(0, 0))
                vertical = False
                y = self.height()
                while y > 0:
                    x = self._side_image.width()
                    while x < self.width():
                        yy = y - self._fg_image.height()
                        p.drawImage(x, yy, self._fg_image.mirrored(False, vertical))
                        x += self._fg_image.width()
                        p.drawImage(x, yy, self._fg_image.mirrored(True, vertical))
                        x += self._fg_image.width() + 1
                    y -= self._fg_image.height()
                    vertical = not vertical
                p.setClipping(False)

            if opt.menuItemType == QStyleOptionMenuItem.Separator:
                # Separator
                p.setPen(menu_style.get_pen_color(opt))
                y = int(act_rect.y() + act_rect.height() / 2)
                p.drawLine(self._side_image.width(), y, act_rect.width(), y)
            else:
                # MenuItem
                self.draw_control(p, opt, act_rect, act.icon(), menu_style)
        pass  # exit for

    def eventFilter(self, obj, event):
        # text = ''
        # if event.type() == QEvent.UpdateRequest:text = 'UpdateRequest'
        # elif event.type() == QEvent.Leave:text = 'Leave'
        # elif event.type() == QEvent.Enter:text = 'Enter'
        # elif event.type() == QEvent.ToolTip:text = 'ToolTip'
        # elif event.type() == QEvent.StatusTip:text = 'StatusTip'
        # elif event.type() == QEvent.ZOrderChange:text = 'ZOrderChange'
        # elif event.type() == QEvent.Show:text = 'Show'
        # elif event.type() == QEvent.ShowToParent:text = 'ShowToParent'
        # elif event.type() == QEvent.UpdateLater:text = 'UpdateLater'
        # elif event.type() == QEvent.MouseMove:text = 'MouseMove'
        # elif event.type() == QEvent.Close:text = 'Close'
        # elif event.type() == QEvent.Hide:text = 'Hide'
        # elif event.type() == QEvent.HideToParent:text = 'HideToParent'
        # elif event.type() == QEvent.Timer:text = 'Timer'
        # elif event.type() == QEvent.Paint:text = 'Paint'
        # elif event.type() == QEvent.MouseButtonPress:
        #     text = 'MouseButtonPress(%d %d)'%(event.globalPos().x(), event.globalPos().y())
        # logging.info("%s %d %s"%(self.title(), event.type(), text))
        if obj == self:
            if event.type() == QEvent.WindowDeactivate:
                self.Hide()
            elif event.type() == QEvent.ToolTip:
                act = self.activeAction()
                if act and act.toolTip() != act.text():
                    QToolTip.showText(event.globalPos(), act.toolTip())
                else:
                    QToolTip.hideText()
        return False
