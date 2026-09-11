"""Station JSON persistence without importing the bot or starting game automation."""
import json
import os
import tempfile
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "json_files"


def load(kind):
    path = DATA_DIR / f"{kind}.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError(f"{path.name} must contain a list of station objects")
    return data


def validate(kind, rows):
    """Return typed copies, preserving extra metadata, and field-level errors."""
    result, errors, names = [], {}, set()
    for index, row in enumerate(rows):
        item = dict(row)
        for key in ("name", "teleporter"):
            value = str(item.get(key, "")).strip()
            item[key] = value
            if not value:
                errors[index, key] = "Enter a station name." if key == "name" else "Enter a teleporter name."
        if item["name"].casefold() in names:
            errors[index, "name"] = "Station names must be unique."
        names.add(item["name"].casefold())
        if kind == "pego":
            try:
                item["delay"] = int(str(item.get("delay", "")))
                if item["delay"] <= 0:
                    raise ValueError
            except ValueError:
                errors[index, "delay"] = "Enter a whole number greater than zero."
        else:
            if item.get("side") not in ("left", "right"):
                errors[index, "side"] = "Choose left or right."
            item["resource_type"] = str(item.get("resource_type", "")).strip()
            if not item["resource_type"]:
                errors[index, "resource_type"] = "Enter a resource type."
        result.append(item)
    return result, errors


def save(kind, rows):
    data, errors = validate(kind, rows)
    if errors:
        raise ValueError("Station fields are invalid")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=4, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, DATA_DIR / f"{kind}.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return data
