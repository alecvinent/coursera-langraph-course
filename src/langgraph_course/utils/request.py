from typing import Any

import requests


def get_json(url: str) -> Any:
    return requests.get(url).json()
