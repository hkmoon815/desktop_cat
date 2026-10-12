from utils import resource_path

class EatAction:
    def __init__(self):
        self.name = "EAT"
        self.frame_count = 7
        self.image_path = resource_path("actions/eat/cat_eat.png")