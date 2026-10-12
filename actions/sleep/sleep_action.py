from utils import resource_path

class SleepAction:
    def __init__(self):
        self.name = "SLEEP"
        self.frame_count = 4  # 잘라둔 4프레임 모션
        self.image_path = resource_path("actions/sleep/cat_sleep.png")
