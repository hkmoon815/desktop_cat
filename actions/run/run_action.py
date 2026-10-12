from utils import resource_path

class RunAction:
    def __init__(self):
        self.name = "RUN"
        self.frame_count = 6
        self.image_path = resource_path("actions/run/cat_run.png")