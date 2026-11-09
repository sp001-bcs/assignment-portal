import json
import os


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, item):
    items = load(path)
    items.append(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
