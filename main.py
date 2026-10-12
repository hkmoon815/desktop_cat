import sys
from PyQt6.QtWidgets import QApplication
from furniture.food.food_item import FoodItem
from furniture.bed.bed_item import BedItem
from furniture.cat_tree.cat_tree_item import CatTreeItem
from furniture.toy.toy_item import ToyItem  # 📍 추가
from cat_widget import CatWidget

# 📍 저장 / 복원 및 부팅 자동 실행 함수 불러오기
from utils import load_settings, save_settings, set_auto_start

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. 부팅 시 자동 실행 등록
    set_auto_start(True)

    # 2. 저장된 위치 정보 불러오기
    saved_data = load_settings() or {}
    cats_data = saved_data.get("cats", {})

    # 가구 객체 생성 (기존 유지)
    furnitures = {
        "FOOD": FoodItem(),
        "BED": BedItem(start_x=1200, start_y=750),
        "CAT_TREE": CatTreeItem(start_x=1400, start_y=600),
        "TOY": ToyItem()  # 📍 낚싯대 아이콘 배치
    }

    # 3. 저장된 좌표가 있으면 불러오고, 없으면 기본 좌표(300, 800 / 600, 800) 사용
    neko1_pos = cats_data.get("Neko1", {"x": 300, "y": 800})
    neko2_pos = cats_data.get("Neko2", {"x": 600, "y": 800})

    cats = [
        # 1번 고양이: 원본 밝기의 머리 (기본값 1.0)
        CatWidget("Mia", start_x=neko1_pos["x"], start_y=neko1_pos["y"], furnitures=furnitures),

        # 2번 고양이: 머리 영역만 40% 어둡게 설정 (head_darkness=0.6)
        CatWidget("Maxi", start_x=neko2_pos["x"], start_y=neko2_pos["y"], furnitures=furnitures, speed_factor=0.55, head_darkness=0.4)
    ]

    # 4. 프로그램 종료 시 두 고양이의 현재 위치를 각각 저장
    def on_exit():
        save_settings({
            "cats": {
                cat.name: {"x": cat.x_pos, "y": cat.y_pos} for cat in cats
            }
        })

    app.aboutToQuit.connect(on_exit)

    sys.exit(app.exec())