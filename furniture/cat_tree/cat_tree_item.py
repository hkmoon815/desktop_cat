from furniture.base_furniture import BaseFurniture
from utils import resource_path


class CatTreeItem(BaseFurniture):
    def __init__(self, start_x, start_y):
        super().__init__(
            item_type="CAT_TREE",
            image_path=resource_path("furniture/cat_tree/cat_tree.png"),
            size=(140, 220),
            start_x=start_x,
            start_y=start_y
        )