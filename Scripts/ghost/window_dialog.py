# coding=utf-8
import logging

from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout, QLabel, QStyleOption, QStyle, \
    QLineEdit, QPushButton

import kikka


class WindowDialog(QWidget):
    DIALOG_MAIN_MENU = 'main_menu'
    DIALOG_TALK = 'talk'
    DIALOG_INPUT = 'input'

    def __init__(self, soul, win_id):
        QWidget.__init__(self)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setMouseTracking(True)
        # self.setAcceptDrops(True)

        self.id = win_id
        self._soul = soul
        self._ghost = self._soul.get_ghost()
        self._window_shell = self._soul.get_window_shell()
        self._frameless_window_hint = True
        self.isFlip = False
        self.setWindowTitle(self._ghost.name)
        self.setContentsMargins(0, 0, 0, 0)

        self._bg_image = None
        self._bg_pix_map = None
        self._bg_mask = None
        self._rect = None

        self._current_page = 0
        self._widgets = {}
        self._talk_label = None
        self._input_line_edit = None
        self._callback = None
        # self.init()

    def initialed(self):
        rect = self._soul.memory_read('DialogRect', [])
        if len(rect) > 0:
            self._rect = QRect(rect[0], rect[1], rect[2], rect[3])
            self.resize(self._rect.size())
        else:
            offset = self._ghost.get_current_shell().setting[self._soul.id].balloon_offset
            self.resize(kikka.const.WindowConst.DialogWindowDefaultSize)
            x = int(offset.x() - self.size().width())
            y = int(-offset.y() )

            rect_data = [x, y, self.size().width(), self.size().height()]
            self._soul.memory_write('DialogRect', rect_data)
            self._rect = QRect(QPoint(x, y), self.size())

        # default control
        self._talk_label = QLabel()
        self._talk_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._talk_label.setWordWrap(True)

        self._inputLabel = QLabel()
        self._input_line_edit = QLineEdit()
        self._inputOk = QPushButton("OK")
        self._inputOk.clicked.connect(self.on_input_ok)
        self._inputCancel = QPushButton("Cancel")
        self._inputCancel.clicked.connect(self.on_input_cancel)

        # default UI
        talk_layout = QVBoxLayout()
        talk_layout.addWidget(self._talk_label)
        talk_widget = QWidget(self)
        talk_widget.setContentsMargins(0, 0, 0, 0)
        talk_widget.setLayout(talk_layout)

        menu_widget = QWidget(self)
        menu_widget.setContentsMargins(0, 0, 0, 0)

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(self._inputOk)
        h_layout.addWidget(self._inputCancel)
        input_layout = QVBoxLayout()
        input_layout.addWidget(self._inputLabel)
        input_layout.addWidget(self._input_line_edit)
        input_layout.addLayout(h_layout)
        input_layout.addStretch()
        input_widget = QWidget(self)
        input_widget.setContentsMargins(0, 0, 0, 0)
        input_widget.setLayout(input_layout)

        self.set_page(self.DIALOG_MAIN_MENU, menu_widget)
        self.set_page(self.DIALOG_TALK, talk_widget)
        self.set_page(self.DIALOG_INPUT, input_widget)

        self._main_layout = QStackedLayout()
        self._main_layout.addWidget(menu_widget)
        self.setLayout(self._main_layout)

    def set_frameless_window_hint(self, boolean):
        self._frameless_window_hint = boolean
        if self._frameless_window_hint is False:
            self.clearMask()
            self.setWindowFlag(Qt.FramelessWindowHint, False)
            self.setWindowOpacity(0.8)
            self.setEnabled(False)

            self.show()
            self.move(2*self.pos().x() - self.geometry().x(), 2*self.pos().y() - self.geometry().y())
            self.update()
            self.activateWindow()
        else:
            self._rect.setX(self.geometry().x() - self._window_shell.pos().x())
            self._rect.setY(self.geometry().y() - self._window_shell.pos().y())
            self._rect.setSize(self.geometry().size())
            rect_data = [self._rect.x(), self._rect.y(), self._rect.width(), self._rect.height()]
            self._soul.memory_write('DialogRect', rect_data)

            pos = QPoint(self.pos().x(), self.pos().y())
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.setWindowOpacity(1)
            self.setEnabled(True)
            self.setMask(self._bg_mask)
            self.show()
            self.move(pos.x(), pos.y())

    def update_position(self):
        if self._frameless_window_hint is False:
            return

        p_pos = self._window_shell.pos()
        p_size = self._soul.get_size()
        new_x = self._rect.x() + p_pos.x()
        new_y = self._rect.y() + p_pos.y()
        self.resize(self._rect.size())

        flip = False
        sw, sh = kikka.helper.get_screen_resolution()
        if new_x + self.width() > sw or new_x < 0:
            flip = True
            new_x = int(p_pos.x()*2 + p_size.width() - new_x - self.width())
            if new_x + self.width() > sw:
                new_x = p_pos.x() - self.width()
            if new_x < 0:
                new_x = p_pos.x() + p_size.width()
        if self.isFlip != flip:
            self.isFlip = flip
            self.repaint()

        super().move(new_x, new_y)

    def set_page(self, tag, qwidget):
        if tag in self._widgets:
            self._widgets[tag].deleteLater()
        qwidget.hide()
        qwidget.setParent(self)
        self._widgets[tag] = qwidget

    def get_talk_label(self):
        return self._talk_label

    def show_input_box(self, title, default='', callback=None):
        self._inputLabel.setText(title)
        self._input_line_edit.setText(default)
        self._callback = callback
        self.show(self.DIALOG_INPUT)

    def show(self, pageTag=None):
        if pageTag is None:
            pageTag = self.DIALOG_MAIN_MENU
        elif pageTag not in self._widgets:
            logging.warning("show: page[%s] not exist" % pageTag)
            pageTag = self.DIALOG_MAIN_MENU

        if self._widgets[pageTag] != self._main_layout.currentWidget():
            self._main_layout.removeWidget(self._main_layout.currentWidget())
            self._main_layout.addWidget(self._widgets[pageTag])
            self._main_layout.setCurrentIndex(0)
            self._current_page = pageTag

        param = kikka.helper.make_ghost_event_param(
            self._ghost.id,
            self._soul.id,
            kikka.const.GhostEvent.Dialog_Show,
            'Show'
        )
        param.data['pageTag'] = self._current_page
        self._ghost.emit_ghost_event(param)

        super().show()
        self.update_position()

    def closeEvent(self, event):
        self.set_frameless_window_hint(True)
        event.ignore()
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        pix_map = QPixmap().fromImage(self._bg_image, Qt.AutoColor)
        painter.drawPixmap(self.rect(), pix_map)

        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        super().paintEvent(event)

    def set_balloon(self, balloon):
        self.setMinimumSize(balloon.minimum_size)
        self.setContentsMargins(balloon.margin[0], balloon.margin[1], balloon.margin[2], balloon.margin[3])
        self.setStyleSheet(balloon.stylesheet)
        self.style().unpolish(self)
        self.style().polish(self)
        self.repaint()

    def set_rect(self, rect):
        self._rect = rect

    def repaint(self):
        self._bg_image = self._ghost.get_balloon_image(self.size(), self.isFlip, self.id)
        self._bg_pix_map = QPixmap().fromImage(self._bg_image, Qt.AutoColor)
        self._bg_mask = self._bg_pix_map.mask()
        super().repaint()

    def talk_clear(self):
        self._talk_label.setText('')

    def on_talk(self, message, speed=50):
        text = self._talk_label.text()
        text += message
        self._talk_label.setText(text)

    def on_input_ok(self):
        if self._callback is not None:
            self._callback(self._input_line_edit.text())
        self.hide()

    def on_input_cancel(self):
        self.hide()
