import json
from pathlib import Path

class TodoStore:
    """Persist todo items in a JSON file."""
    def __init__(self, path: str):
        self.path = Path(path)
        self.items = json.loads(self.path.read_text()) if self.path.exists() else []

    def add(self, title: str, priority: int = 1) -> dict:
        item = {"id": len(self.items) + 1, "title": title, "priority": priority, "done": False}
        self.items.append(item)
        self.save()
        return item

    def complete(self, item_id: int) -> bool:
        for i in self.items:
            if i["id"] == item_id:
                i["done"] = True
                self.save()
                return True
        return False

    def save(self) -> None:
        self.path.write_text(json.dumps(self.items, indent=2))
