# coding=utf-8
import os
import time
import ctypes
import logging
import win32gui
import win32con
import win32api
import threading
import pywintypes

from PyQt5.QtGui import QPainter, QIcon
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QWidget

import kikka
from kikka.helper import Singleton


class KikkaApp(Singleton):
    isDebug = False

    def __init__(self):
        self._loading_window = LoadingWindow()
        self._timer = QTimer()

        logging.info("")
        logging.info("Hey~ Kikka here %s" % ("-" * 40))
        kikka.memory.awake(kikka.const.KikkaMemoryFileName)

    def _load(self):
        time.sleep(1)

        # start
        kikka.ghost.scan_ghost(kikka.path.GHOSTS)

        kikka.core.start()
        kikka.app.start()

        if kikka.ghost.get_ghost_count() <= 0:
            logging.warning('no search ghost!')
            self.exit_app()
            return

        gid = kikka.core.add_ghost(kikka.ghost.get_ghost(0))
        kikka.menu.set_app_menu(kikka.core.get_ghost(gid).get_soul(0).get_menu())

        logging.info('kikka load done %s' % ("-" * 40))
        self._loading_window.close()
        kikka.core.show()
        kikka.core.on_boot()

    def awake(self):
        self._loading_window.show()
        self._timer.timeout.connect(self._load)
        self._timer.setSingleShot(True)
        self._timer.start(100)

    def start(self):
        self._create_guard_thread()
        self._create_tray_icon()

    def exit_app(self):
        app = QApplication.instance()
        app.exit(0)

        kikka.memory.close()
        logging.info("Bye Bye~")

    def _create_guard_thread(self):
        try:
            guard = Guard()
            t1 = threading.Thread(target=guard.run)
            t1.setDaemon(True)
            t1.start()
        except Exception:
            logging.exception("error:create guard thread fail")

    def _create_tray_icon(self):
        app = QApplication.instance()
        icon = QIcon(os.path.join(kikka.path.IMAGE, "icon.ico"))
        app.setWindowIcon(icon)

        app.trayIcon = QSystemTrayIcon(app)
        app.trayIcon.setIcon(icon)
        app.trayIcon.show()
        app.trayIcon.activated.connect(self._tray_icon_activated)

    def _tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if kikka.core.get_state() == kikka.core.APP_STATE.HIDE:
                kikka.core.set_state(kikka.core.APP_STATE.SHOW)
            else:
                kikka.core.set_state(kikka.core.APP_STATE.HIDE)
        pass


class LoadingWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self._image = kikka.helper.get_image(os.path.join(kikka.path.IMAGE, "loading.png"))
        self.resize(self._image.width(), self._image.height())
        (w, h) = kikka.helper.get_screen_client_rect()
        self.move(w-self._image.width(), h-self._image.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(self.rect(), self._image)
        super().paintEvent(event)


class Guard(Singleton):
    def __init__(self):
        self._has_full_screen_progress = False
        self._has_kikka_exe = True

    def run(self):
        try:
            time.sleep(1)

            width = 0
            height = 0
            while True:
                self._watch_full_screen_progress()
                width, height = self._watch_screen_client_size_change(width, height)
                time.sleep(3)
        except Exception:
            logging.exception("error: _guard error")
        logging.warning("_guard thread exit!")

    def _enum_windows_callback(self, hwnd, extra):
        class_name = win32gui.GetClassName(hwnd)
        if class_name != "WorkerW":
            return True
        child = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", "")
        if child == 0:
            return True
        extra.append(win32gui.FindWindowEx(child, 0, "SysListView32", "FolderView"))
        return False

    def _get_desktop_hwnd(self):
        dt_hwnd = win32gui.GetDesktopWindow()
        shell_hwnd = ctypes.windll.user32.GetShellWindow()
        shell_dll_def_view = win32gui.FindWindowEx(shell_hwnd, 0, "SHELLDLL_DefView", "")

        if shell_dll_def_view == 0:
            sys_list_view_container = []
            try:
                win32gui.EnumWindows(self._enum_windows_callback, sys_list_view_container)
            except pywintypes.error as e:
                if e.winerror != 0:
                    err = win32api.GetLastError()
                    logging.warning("_get_desktop_hwnd Fail: %d" % err)
                    return [None]

            if len(sys_list_view_container) > 0:
                sys_list_view = sys_list_view_container[0]
                shell_dll_def_view = win32gui.GetParent(sys_list_view)
            else:
                sys_list_view = 0
        else:
            sys_list_view = win32gui.FindWindowEx(shell_dll_def_view, 0, "SysListView32", "FolderView")
        worker_w = win32gui.GetParent(shell_dll_def_view) if shell_dll_def_view != 0 else 0
        return [dt_hwnd, shell_hwnd, worker_w, shell_dll_def_view, sys_list_view]

    def _watch_full_screen_progress(self):
        has_full_screen_progress = False
        try:
            sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            fg_hwnd = win32gui.GetForegroundWindow()
            ignore_hwnd = self._get_desktop_hwnd()
        except Exception:
            logging.exception("error: _watchFullScreenProgress get hwnd fail")
            return

        if fg_hwnd not in ignore_hwnd:
            try:
                fg_rect = win32gui.GetWindowRect(fg_hwnd)
                if fg_rect[0] == 0 and fg_rect[1] == 0 and fg_rect[2] == sw and fg_rect[3] == sh:
                    has_full_screen_progress = True

            except Exception:
                has_full_screen_progress = False

        core_state = kikka.core.get_state()
        if has_full_screen_progress and core_state == kikka.core.APP_STATE.SHOW:
            kikka.core.signal.SetState.emit(kikka.core.APP_STATE.FULL_SCREEN)
        elif not has_full_screen_progress and core_state == kikka.core.APP_STATE.FULL_SCREEN:
            kikka.core.signal.SetState.emit(kikka.core.APP_STATE.SHOW)

    def _watch_screen_client_size_change(self, old_width, old_height):
        rect = QApplication.instance().desktop().availableGeometry()
        width = rect.width()
        height = rect.height()
        if width != old_width or height != old_height:
            kikka.core.signal.ScreenClientSizeChange.emit()
        return width, height
