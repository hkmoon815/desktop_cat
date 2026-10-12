# actions/climb/climb_action.py
from utils import resource_path

class ClimbAction:
    def __init__(self):
        # 벽 타기 전용 수직/기어가는 스프라이트 이미지 경로
        self.image_path = resource_path("actions/climb/climb.png")