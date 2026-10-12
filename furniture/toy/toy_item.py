from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QPixmap, QImage, QColor, QPainter
from PyQt6.QtWidgets import QWidget, QApplication
from furniture.base_furniture import BaseFurniture
from utils import resource_path


class ToyOverlay(QWidget):
    """낚싯대 활성화 시 화면 전체를 덮어 마우스 커서를 지속시켜주는 투명 오버레이"""

    def __init__(self, parent_toy):
        super().__init__()
        self.parent_toy = parent_toy
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 전체 모니터 영역 크기로 설정
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def mousePressEvent(self, event):
        # 화면 어디든 한 번 더 클릭하면 낚싯대 커서 해제
        self.parent_toy.toggle_toy_cursor()

    def paintEvent(self, event):
        # 완전히 투명하지만 마우스 이벤트를 수신할 수 있도록 최소 알파값(1) 설정
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))


class ToyItem(BaseFurniture):
    def __init__(self, start_x=None, start_y=None):
        size_w, size_h = 130, 60

        screen = QApplication.primaryScreen().availableGeometry()
        if start_x is None:
            start_x = screen.width() - size_w - 70
        if start_y is None:
            start_y = screen.height() - size_h - 70

        super().__init__(
            item_type="TOY",
            image_path=resource_path("furniture/toy/toy.png"),
            size=(size_w, size_h),
            start_x=start_x,
            start_y=start_y,
            stays_on_top=False  # 📍 밥그릇처럼 다른 창 위에 떠있지 않도록 설정
        )
        self.is_active = False
        self.overlay = None

        # 하얀색 배경 강제 제거 & 투명화 전처리
        original_image = QImage(self.image_path)
        if not original_image.isNull():
            image_with_alpha = original_image.convertToFormat(QImage.Format.Format_ARGB32)
            for x in range(image_with_alpha.width()):
                for y in range(image_with_alpha.height()):
                    pixel_color = image_with_alpha.pixelColor(x, y)
                    if pixel_color.red() > 240 and pixel_color.green() > 240 and pixel_color.blue() > 240:
                        image_with_alpha.setPixelColor(x, y, QColor(0, 0, 0, 0))

            self.pixmap = QPixmap.fromImage(image_with_alpha)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_toy_cursor()

    def toggle_toy_cursor(self):
        if not self.is_active:
            # 1. 화면 전체 투명 레이어 생성 및 활성화
            if not self.overlay:
                self.overlay = ToyOverlay(self)
            self.overlay.show()
            self.overlay.raise_()

            # 2. 낚싯대 커서 적용
            scaled_cursor_pix = self.pixmap.scaled(
                48, 22,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            custom_cursor = QCursor(scaled_cursor_pix, 0, 0)
            QApplication.setOverrideCursor(custom_cursor)
            self.is_active = True
        else:
            # 1. 투명 레이어 숨기기
            if self.overlay:
                self.overlay.hide()

            # 2. 원래 마우스 커서로 복구
            QApplication.restoreOverrideCursor()
            self.is_active = False