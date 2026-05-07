import json
import os
from typing import List

_CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.spotify-skip-permissions', 'config.json')


def load_config() -> dict:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_config(data: dict):
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_folders() -> List[str]:
    return load_config().get('folders', [])


def save_folders(folders: List[str]):
    cfg = load_config()
    cfg['folders'] = folders
    save_config(cfg)
