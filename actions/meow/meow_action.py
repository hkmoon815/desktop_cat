import os
import random
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect
from utils import resource_path


class MeowAction:
    def __init__(self):
        self.name = "MEOW"
        self.image_path = resource_path("actions/meow/cat_meow.png")

        # 📍 랜덤 재생할 야옹 소리 파일 경로 2개 등록
        self.sound_paths = [
            resource_path("actions/meow/cat_meow1.wav"),
            resource_path("actions/meow/cat_meow2.wav")
        ]

        # PyQt6 크로스플랫폼 사운드 플레이어 생성
        self.sound_effect = QSoundEffect()

    def play_sound(self):
        """ 야옹 트리거 호출 시 2개 파일 중 하나를 무작위 선택하여 재생 """
        chosen_path = random.choice(self.sound_paths)

        if os.path.exists(chosen_path):
            self.sound_effect.setSource(QUrl.fromLocalFile(chosen_path))
            self.sound_effect.setVolume(0.8)  # 볼륨 설정 (0.0 ~ 1.0)
            self.sound_effect.play()