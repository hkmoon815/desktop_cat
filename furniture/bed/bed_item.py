from furniture.base_furniture import BaseFurniture
from utils import resource_path


class BedItem(BaseFurniture):
    def __init__(self, start_x, start_y):
        super().__init__(
            item_type="BED",
            image_path=resource_path("furniture/bed/bed.png"),
            size=(120, 100),
            start_x=start_x,
            start_y=start_y
        )