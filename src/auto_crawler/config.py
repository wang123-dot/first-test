from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

import yaml


@dataclass
class AppConfig:
    data: Dict[str, Any]

    @staticmethod
    def load(path: str) -> "AppConfig":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return AppConfig(data=data)

    def get(self, *keys: str, default: Any = None) -> Any:
        cur: Any = self.data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    @property
    def base_url(self) -> str:
        return str(self.get("site", "base_url", default="")).rstrip("/")

    @property
    def credentials(self) -> Dict[str, Any]:
        return dict(self.get("credentials", default={}))
