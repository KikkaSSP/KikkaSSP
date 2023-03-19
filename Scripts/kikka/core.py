# coding=utf-8
import time
import random
import logging
import datetime
from enum import Enum

from PyQt5.QtCore import QTimer, QObject, pyqtSignal

import kikka
from kikka.helper import Singleton


class KikkaCoreSignal(QObject):
    SetState = pyqtSignal(int)
    Hide = pyqtSignal()
    Show = pyqtSignal()
    ScreenClientSizeChange = pyqtSignal()


class KikkaCore(Singleton):
    isDebug = False

    class APP_STATE:
        HIDE = 0
        SHOW = 1
        FULL_SCREEN = 2

    def __init__(self):
        self._app_state = KikkaCore.APP_STATE.SHOW
        self._last_clock = time.clock()
        self._is_need_update = True
        self._ghosts = {}

        self.signal = KikkaCoreSignal()
        self.signal.SetState.connect(self.set_state)
        self.signal.Show.connect(self.show)
        self.signal.Hide.connect(self.hide)
        self.signal.ScreenClientSizeChange.connect(self.screen_client_size_change)

        kikka.memory.create_table("kikka_core")
        self._run_timer = QTimer()
        self._run_timer.setSingleShot(False)
        self._timer_interval = 10
        self.set_timer_interval(self._timer_interval)

    def set_state(self, state):
        if state == KikkaCore.APP_STATE.HIDE or state == KikkaCore.APP_STATE.FULL_SCREEN:
            self.hide()
        elif state == KikkaCore.APP_STATE.SHOW:
            self.show()
        else:
            logging.warning("set_state fail: unknown state: %d" % state)
            return
        self._app_state = state

    def get_state(self):
        return self._app_state

    def on_boot(self):
        for _, g in self._ghosts.items():
            g.on_boot()

    def show(self):
        self._app_state = KikkaCore.APP_STATE.SHOW
        for _, g in self._ghosts.items():
            g.show()
        self.start()

    def hide(self):
        self._app_state = KikkaCore.APP_STATE.HIDE
        self.stop()
        for _, g in self._ghosts.items():
            g.hide()

    def screen_client_size_change(self):
        self._app_state = KikkaCore.APP_STATE.SHOW
        for _, g in self._ghosts.items():
            g.reset_windows_position(False)
        self.start()

    def add_ghost(self, ghost):
        self._ghosts[ghost.id] = ghost
        if not ghost.initialized:
            ghost.init()
        if ghost.initialized:
            ghost.initialed()
        return ghost.id

    def get_ghost(self, gid):
        if gid in self._ghosts:
            return self._ghosts[gid]
        else:
            logging.error("getGhost: gid NOT in ghost list")
            raise ValueError

    def set_ghost_surface(self, ghost_id, soul_id, surface_id):
        if ghost_id in self._ghosts:
            self._ghosts[ghost_id].set_surface(soul_id, surface_id)

    def set_ghost_shell(self, ghost_id, shell_id):
        if ghost_id in self._ghosts:
            self._ghosts[ghost_id].set_shell(shell_id)

    def start(self):
        self._last_clock = time.clock()
        self._run_timer.timeout.connect(self.run)
        self._run_timer.start(self._timer_interval)

    def stop(self):
        self._run_timer.stop()

    def set_timer_interval(self, interval):
        self._timer_interval = interval
        self._run_timer.setInterval(interval)

    def get_timer_interval(self):
        return self._timer_interval

    def run(self):
        try:
            now_clock = time.clock()
            update_time = (now_clock - self._last_clock) * 1000

            for gid, ghost in self._ghosts.items():
                ghost.on_update(update_time)

            self._last_clock = now_clock
        except Exception:
            logging.exception('Core.run: run time error')
            raise SyntaxError('run time error')
        self._is_need_update = False

    def repaint_all_ghost(self):
        for _, g in self._ghosts.items():
            g.repaint()

    def get_property(self, key):
        now = datetime.datetime.now()
        if key == '':
            return None
        elif key == 'system.year':
            return now.year
        elif key == 'system.month':
            return now.month
        elif key == 'system.day':
            return now.day
        elif key == 'system.hour':
            return now.hour
        elif key == 'system.minute':
            return now.minute
        elif key == 'system.second':
            return now.second
        elif key == 'system.millisecond':
            return now.microsecond
        elif key == 'system.dayofweek':
            return now.weekday()

        elif key == 'ghostlist.count':
            return len(self._ghosts)
        else:
            logging.warning("getProperty: Unknown Key")
            return None
