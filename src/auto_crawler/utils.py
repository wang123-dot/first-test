from __future__ import annotations

import datetime as _dt
import random
import re
from typing import Dict, Iterable, List, Optional

from bs4 import BeautifulSoup, Tag


def now_str() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ts_until(target_dt_str: Optional[str]) -> float:
    if not target_dt_str:
        return 0.0
    try:
        target = _dt.datetime.strptime(target_dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # 兼容常见格式：YYYY/MM/DD HH:MM:SS
        target = _dt.datetime.strptime(target_dt_str.replace("/", "-"), "%Y-%m-%d %H:%M:%S")
    delta = (target - _dt.datetime.now()).total_seconds()
    return max(0.0, delta)


def pick_text(tag: Optional[Tag]) -> str:
    if not tag:
        return ""
    return tag.get_text(strip=True)


def absolute_url(href: str, base_url: str) -> str:
    if not href:
        return href
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if not href.startswith("/"):
        href = "/" + href
    return base_url.rstrip("/") + href


def str_contains_any(s: str, keywords: Iterable[str]) -> bool:
    s = s or ""
    for k in keywords:
        if k and k in s:
            return True
    return False


def clean_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def random_delay(a: float = 0.15, b: float = 0.5) -> float:
    return random.uniform(a, b)


def extract_hidden_inputs(form: Tag) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        if inp.get("type", "").lower() in {"hidden", "text", "password"}:
            data[name] = inp.get("value", "")
    return data


def choose_radio_value(options: List[Tag], strategy: str = "max") -> Optional[str]:
    values = [(opt.get("value") or "", opt) for opt in options]
    if not values:
        return None
    # 优先按数值排序
    numeric = [(float(v[0]), v[0]) for v in values if re.fullmatch(r"-?\d+(\.\d+)?", v[0] or "")]
    if strategy == "first":
        return values[0][0]
    if strategy == "last":
        return values[-1][0]
    if strategy == "max" and numeric:
        numeric.sort(key=lambda x: x[0])
        return numeric[-1][1]
    # 无数值时取最后一个
    return values[-1][0]


def choose_select_value(options: List[Tag], strategy: str = "last") -> Optional[str]:
    candidates = [opt.get("value") or "" for opt in options if (opt.get("value") or "").strip() != ""]
    if not candidates:
        return None
    if strategy == "first":
        return candidates[0]
    # 默认 last
    return candidates[-1]
