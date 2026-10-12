from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from furniture.base_furniture import BaseFurniture
from utils import resource_path


class FoodItem(BaseFurniture):
    def __init__(self, start_x=None, start_y=None):
        size_w, size_h = 80, 80

        screen = QApplication.primaryScreen().availableGeometry()
        margin_x = 40

        if start_x is None:
            start_x = screen.width() - size_w - margin_x
        if start_y is None:
            start_y = screen.height() - size_h

        super().__init__(
            item_type="FOOD",
            image_path=resource_path("furniture/food/food.png"),
            size=(size_w, size_h),
            start_x=start_x - 80,
            start_y=start_y + 25,
            stays_on_top=False
        )
        self.cats = []

    def register_cat(self, cat):
        """ 고양이 객체를 밥그릇 등록 리스트에 추가 """
        if cat not in self.cats:
            self.cats.append(cat)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            # 밥그릇을 클릭하면 모든 고양이에게 밥 먹으러 이동 명령
            for cat in self.cats:
                cat.go_to_eat()

# furniture/food/food_item.py 의 mousePressEvent
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
             # 📍 첫 번째 고양이는 왼쪽(-1), 두 번째 고양이는 오른쪽(1) 지정
            sides = [-1, 1]
            for i, cat in enumerate(self.cats):
                side = sides[i % len(sides)]
                cat.go_to_eat(side=side)