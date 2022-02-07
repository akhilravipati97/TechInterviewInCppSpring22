from util.common import fail
from util.log import get_logger

LOG = get_logger("User")

class User:
    def __init__(self, name: str, uni: str, usr_id_map: dict) -> None:
        self.name = name
        self.usr_id_map = usr_id_map
        self.user_id = uni
        self.uni = uni

    
    def handle(self, platform_name: str) -> str:
        if platform_name not in self.usr_id_map:
            fail(f"user: [{self.name}] does not have a handle for [{platform_name}]", LOG)
        return self.usr_id_map[platform_name]