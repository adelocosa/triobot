from typing import Any


from typing import Any


class User:
    def __init__(self, data: dict[str, Any]):
        self.id: int = int(data["id"])
        self.username: str = data["username"]
        self.number: int = int(data["discriminator"])
