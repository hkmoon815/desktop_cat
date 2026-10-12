from utils import resource_path

class IdleAction:
    def __init__(self):
        self.name = "IDLE"
        self.image_path = resource_path("actions/idle/cat_idle.png")