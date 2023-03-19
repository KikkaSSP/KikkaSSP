# coding=utf-8
import logging
import math

from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QCursor
from PyQt5.QtWidgets import QWidget

import kikka
from kikka.const import GhostEvent


class WindowShell(QWidget):
    def __init__(self, soul, win_id):
        QWidget.__init__(self)
        self._soul = soul
        self._ghost = self._soul.get_ghost()
        self.id = win_id

        self._is_moving = False
        self._offset = QPoint(0, 0)
        self._boxes = {}
        self._move_pos = QPoint(0, 0)
        self._mouse_pos = QPoint(0, 0)
        self._pix_map = None
        self._touch_type = None
        self._touch_place = None
        self._touch_tick = 0

        self._init()

    def _init(self):
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        # self.setContextMenuPolicy(Qt.ActionsContextMenu)

    def set_boxes(self, boxes, offset):
        self._boxes = {}
        self._offset = offset
        for cid, col in boxes.items():
            rect = col.rect
            rect.moveTopLeft(col.rect.topLeft() + offset)
            self._boxes[cid] = (rect, col.tag)

    def _box_collision(self, event_type, event):
        if self._is_moving is True:
            return

        mx = self._mouse_pos.x()
        my = self._mouse_pos.y()
        for cid, box in self._boxes.items():
            rect = box[0]
            if rect.contains(mx, my) is False:
                continue

            tag = box[1]
            param = kikka.helper.make_ghost_event_param(self._ghost.id, self._soul.id, event_type, tag)
            param.data['ShellWindowID'] = self.id
            param.data['QEvent'] = event
            self._ghost.emit_ghost_event(param)

            # Touch
            if self._touch_type == event_type and self._touch_place == tag:
                self._touch_tick += 1
            else:
                self._touch_tick = 1
                self._touch_type = event_type
                self._touch_place = tag

            touch_area = rect.width() * rect.height()
            request_tick = max(30.0, math.sqrt(touch_area))
            # print(self._touchTick, request_tick)
            if self._touch_tick > request_tick:
                self._touch_tick = 0
                param.event_type = GhostEvent.Shell_MouseTouch
                param.event_tag = tag
                self._ghost.emit_ghost_event(param)
            return tag

        param = kikka.helper.make_ghost_event_param(self._ghost.id, self._soul.id, event_type, 'None')
        param.data['ShellWindowID'] = self.id
        param.data['QEvent'] = event
        self._ghost.emit_ghost_event(param)
        return None

    def _mouse_logging(self, event, button, x, y):
        if kikka.core.isDebug:
            page_sizes = dict((n, x) for x, n in vars(Qt).items() if isinstance(n, Qt.MouseButton))
            logging.debug("%s %s (%d, %d)", event, page_sizes[button], x, y)

    def get_mouse_pose(self):
        return self._move_pos.x(), self._move_pos.y()

    def save_shell_rect(self):
        rect = [self.pos().x(), self.pos().y(), self.size().width(), self.size().height()]
        self._soul.memory_write('ShellRect', rect)

    def debug_draw(self, image):

        def drawText(_painter, _line, _left, msg, color=Qt.white):
            _painter.setPen(color)
            _painter.drawText(_left, _line*12, msg)
            return _line+1

        def drawPoint(_painter, point, color=Qt.red):
            _painter.setPen(color)
            _painter.drawEllipse(QRect(point.x() - 5, point.y() - 5, 10, 10))
            _painter.drawPoint(point.x(), point.y())

        shell = self._ghost.get_current_shell()
        shell_offset = shell.get_offset(self._soul.id)
        center_pos = self._soul.get_center_point()
        draw_offset = self._soul.get_draw_offset()

        img = QImage(image.width()+250, max(image.height()+1, 120), QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(img)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(0, 0, img.width(), img.height(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.drawImage(QPoint(), image)

        if kikka.core.isDebug is True:
            painter.fillRect(QRect(image.width(), 0, 250, img.height()), QColor(0, 0, 0, 255))
            painter.setPen(Qt.white)
            painter.drawRect(QRect(0, 0, image.width(), image.height()))

            left = image.width() + 3
            line = 1
            line = drawText(painter, line, left, "ghost ID: %d" % self._ghost.id)
            line = drawText(painter, line, left, "Name: %s" % self._ghost.name)
            line = drawText(painter, line, left, "Soul ID: %d" % self._soul.id)
            line = drawText(painter, line, left, "surface: %d" % self._soul.get_current_surface_id())
            line = drawText(painter, line, left, "bind: %s" % shell.get_bind(self._soul.id))
            line = drawText(painter, line, left, "animations: %s" % self._soul.get_running_animation())
            line = drawText(painter, line, left, "shell offset: %d %d" % (shell_offset.x(), shell_offset.y()), Qt.green)
            line = drawText(painter, line, left, "draw offset: %d %d" % (draw_offset.x(), draw_offset.y()), Qt.blue)
            line = drawText(painter, line, left, "surface center: %d %d" % (center_pos.x(), center_pos.y()), Qt.red)

        if kikka.ghost.isDebug is True:
            painter.setPen(Qt.blue)
            painter.drawRect(self._soul.get_base_rect().translated(draw_offset))

            drawPoint(painter, shell_offset, Qt.green)
            drawPoint(painter, draw_offset, Qt.blue)
            drawPoint(painter, center_pos, Qt.red)

            surface = self._soul.get_current_surface()
            if surface is not None:
                for cid, col in surface.collision_boxes.items():
                    painter.setPen(Qt.red)
                    rect = col.rect
                    rect.moveTopLeft(col.rect.topLeft() + draw_offset)
                    painter.drawRect(rect)
                    painter.fillRect(rect, QColor(255, 255, 255, 64))
                    painter.setPen(Qt.black)
                    painter.drawText(rect, Qt.AlignCenter, col.tag)
            pass
        painter.end()
        return img

    def set_image(self, image):
        if kikka.core.isDebug | kikka.ghost.isDebug:
            image = self.debug_draw(image)
        pix_map = QPixmap().fromImage(image, Qt.AutoColor)
        self._pix_map = pix_map

        self.setFixedSize(self._pix_map.size())
        self.setMask(self._pix_map.mask())
        self.repaint()

    # ##############################################################################################################
    # Event

    # def eventFilter(self, obj, event):
    #     text = ''
    #     if event.type() == QEvent.UpdateRequest:text = 'UpdateRequest'
    #     elif event.type() == QEvent.Leave:text = 'Leave'
    #     elif event.type() == QEvent.Enter:text = 'Enter'
    #     elif event.type() == QEvent.ToolTip:text = 'ToolTip'
    #     elif event.type() == QEvent.StatusTip:text = 'StatusTip'
    #     elif event.type() == QEvent.ZOrderChange:text = 'ZOrderChange'
    #     elif event.type() == QEvent.Show:text = 'Show'
    #     elif event.type() == QEvent.ShowToParent:text = 'ShowToParent'
    #     elif event.type() == QEvent.UpdateLater:text = 'UpdateLater'
    #     elif event.type() == QEvent.MouseMove:text = 'MouseMove'
    #     elif event.type() == QEvent.Close:text = 'Close'
    #     elif event.type() == QEvent.Hide:text = 'Hide'
    #     elif event.type() == QEvent.HideToParent:text = 'HideToParent'
    #     elif event.type() == QEvent.Timer:text = 'Timer'
    #     elif event.type() == QEvent.Paint:text = 'Paint'
    #     elif event.type() == QEvent.Move:text = 'Move'
    #     elif event.type() == QEvent.InputMethodQuery:text = 'InputMethodQuery';self._InputMethodQuery = event
    #     elif event.type() == QEvent.MouseButtonPress:
    #         text = 'MouseButtonPress(%d %d)' % (event.globalPos().x(), event.globalPos().y())
    #
    #     logging.info("%s %d %s"%("MainWindow", event.type(), text))
    #     return False

    def contextMenuEvent(self, event):
        # logging.info('contextMenuEvent')
        self._soul.show_menu(event.globalPos())

    def mousePressEvent(self, event):
        self._mouse_logging("mousePressEvent", event.buttons(), event.globalPos().x(), event.globalPos().y())
        self._move_pos = event.globalPos() - self.pos()
        if event.buttons() == Qt.LeftButton:
            self._is_moving = True
            event.accept()

        self._box_collision(GhostEvent.Shell_MouseDown, event)

    def mouseMoveEvent(self, event):
        # self._mouseLogging("mouseMoveEvent", event.buttons(), event.globalPos().x(), event.globalPos().y())
        self._mouse_pos = event.pos()
        if self._is_moving and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._move_pos)

            self._soul.get_dialog().update_position()
            event.accept()
        else:
            self._is_moving = False

        tag = self._box_collision(GhostEvent.Shell_MouseMove, event)
        if tag == 'Bust':
            self.setCursor(QCursor(Qt.OpenHandCursor))
        elif tag is None:
            self.setCursor(QCursor(Qt.ArrowCursor))
        else:
            self.setCursor(QCursor(Qt.PointingHandCursor))

    def mouseReleaseEvent(self, event):
        self._mouse_logging("mouseReleaseEvent", event.buttons(), event.globalPos().x(), event.globalPos().y())
        self._is_moving = False
        self.save_shell_rect()

        self._box_collision(GhostEvent.Shell_MouseUp, event)

    def mouseDoubleClickEvent(self, event):
        self._mouse_logging("mouseDoubleClickEvent", event.buttons(), event.globalPos().x(), event.globalPos().y())
        if event.buttons() == Qt.LeftButton:
            self._is_moving = False

        self._box_collision(GhostEvent.Shell_MouseDoubleClick, event)

    def wheelEvent(self, event):
        # self._mouseLogging("wheelEvent", btn, event.pos().x(), event.pos().y())
        self._box_collision(GhostEvent.Shell_WheelEvent, event)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            logging.info("drop file: %s" % url.toLocalFile())
        pass

    def move(self, *__args):
        if len(__args) == 1 and isinstance(__args[0], QPoint):
            x = __args[0].x()
            y = __args[0].y()
        elif len(__args) == 2 and isinstance(__args[0], int) and isinstance(__args[1], int):
            x = __args[0]
            y = __args[1]
        else:
            super().move(*__args)
            return

        if self._ghost.get_is_lock_on_task_bar() is True:
            y = kikka.helper.get_screen_client_rect()[1] - self.height()
        super().move(x, y)

    ###############################################################################################################
    # paint event

    def show(self):
        param = kikka.helper.make_ghost_event_param(
            self._ghost.id,
            self._soul.id,
            kikka.const.GhostEvent.Shell_Show,
            'Show'
        )
        self._ghost.emit_ghost_event(param)

        super().show()
        self.move(self.pos())

    def paintEvent(self, event):
        if self._pix_map is None:
            return
        painter = QPainter(self)
        painter.drawPixmap(QPoint(), self._pix_map)
