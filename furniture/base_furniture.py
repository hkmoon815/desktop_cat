from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QWidget


class BaseFurniture(QWidget):
    def __init__(self, item_type, image_path, size, start_x, start_y, stays_on_top=True):
        super().__init__()
        self.item_type = item_type
        self.image_path = image_path
        self.item_w, self.item_h = size

        # 📍 stays_on_top 옵션에 따라 WindowStaysOnTopHint 플래그 적용
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if stays_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.resize(self.item_w, self.item_h)
        self.pixmap = QPixmap(self.image_path)
        self.x_pos = float(start_x)
        self.y_pos = float(start_y)
        self.move(int(self.x_pos), int(self.y_pos))

        self.drag_start = QPoint()
        self.show()

    def get_center_pos(self):
        """고양이가 가구로 찾아갈 중심 좌표 반환"""
        return self.x_pos + self.width() / 2, self.y_pos + self.height() / 2

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.pos() - self.drag_start
            self.x_pos += delta.x()
            self.y_pos += delta.y()
            self.move(int(self.x_pos), int(self.y_pos))

    def paintEvent(self, event):
        if not self.pixmap.isNull():
            painter = QPainter(self)
            scaled = self.pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)