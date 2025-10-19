from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .http import HttpClient
from .utils import (
    choose_radio_value,
    choose_select_value,
    extract_hidden_inputs,
    now_str,
    pick_text,
    random_delay,
)


def _open_list(client: HttpClient, path: str) -> BeautifulSoup:
    resp, soup = client.fetch_soup(path)
    if resp.status_code >= 400:
        raise RuntimeError(f"评教列表页请求失败: {resp.status_code}")
    return soup


def _parse_items(soup: BeautifulSoup, cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    sel = cfg.get("item_selector")
    parse_cfg = cfg.get("parse") or {}
    for row in soup.select(sel):
        item: Dict[str, str] = {}
        for key, rule in parse_cfg.items():
            el = row.select_one(rule.get("selector"))
            attr = rule.get("attr", "text")
            if not el:
                item[key] = ""
                continue
            if attr == "text":
                item[key] = pick_text(el)
            else:
                item[key] = el.get(attr, "")
        items.append(item)
    return items


def _fill_form(form: Any, strategy: Dict[str, Any]) -> Dict[str, str]:
    data: Dict[str, str] = extract_hidden_inputs(form)

    # radio groups
    radios_by_name: Dict[str, List[Any]] = {}
    for inp in form.find_all("input"):
        if inp.get("type", "").lower() == "radio" and inp.get("name"):
            radios_by_name.setdefault(inp["name"], []).append(inp)

    for name, options in radios_by_name.items():
        val = choose_radio_value(options, strategy.get("radio", "max"))
        if val is not None:
            data[name] = val

    # checkbox
    checkbox_strategy = strategy.get("checkbox", "none")
    if checkbox_strategy == "all":
        for inp in form.find_all("input"):
            if inp.get("type", "").lower() == "checkbox" and inp.get("name"):
                data.setdefault(inp["name"], inp.get("value", "on"))

    # select
    for sel in form.find_all("select"):
        name = sel.get("name")
        if not name:
            continue
        options = sel.find_all("option")
        val = choose_select_value(options, strategy.get("select", "last"))
        if val is not None:
            data[name] = val

    # textarea
    text_default = strategy.get("textarea", "老师讲课认真负责。")
    for ta in form.find_all("textarea"):
        name = ta.get("name")
        if not name:
            continue
        data[name] = text_default

    return data


def _submit_form(client: HttpClient, form: Any, data: Dict[str, str]) -> str:
    action = form.get("action") or ""
    method = (form.get("method") or "POST").upper()
    if method == "GET":
        resp = client.get(action, params=data)
    else:
        resp = client.post(action, data=data)
    return resp.text


def run_evaluate(client: HttpClient, cfg: Dict[str, Any]) -> None:
    ev_cfg = cfg.get("site", {}).get("evaluate", {})
    if not ev_cfg or not ev_cfg.get("enabled", True):
        print(f"[{now_str()}] 评教功能未启用，跳过")
        return

    list_path = ev_cfg.get("list_path")
    soup = _open_list(client, list_path)

    items = _parse_items(soup, ev_cfg)
    print(f"[{now_str()}] 解析到需评教数量: {len(items)}")

    strategy = ev_cfg.get("strategy") or {}
    success_cfg = ev_cfg.get("success") or {}

    for idx, item in enumerate(items, 1):
        print(f"[{now_str()}] 处理评教({idx}/{len(items)}): {item.get('id')} {item.get('name')}")
        link = item.get("link")
        if not link:
            print(f"[{now_str()}] 缺少评教链接，跳过")
            continue
        resp, page = client.fetch_soup(link)
        form = page.select_one(ev_cfg.get("form_selector") or "form")
        if not form:
            print(f"[{now_str()}] 未找到评教表单，跳过")
            continue
        data = _fill_form(form, strategy)
        html = _submit_form(client, form, data)
        passed = any((kw in html) for kw in (success_cfg.get("text_contains") or []))
        if passed or not (success_cfg.get("text_contains")):
            print(f"[{now_str()}] 提交成功：{item.get('id')} {item.get('name')}")
        else:
            print(f"[{now_str()}] 提交未确认成功，请手动检查：{item.get('id')} {item.get('name')}")
        client.sleep(random_delay())
