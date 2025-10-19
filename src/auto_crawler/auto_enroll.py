from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .http import HttpClient
from .utils import (
    absolute_url,
    clean_space,
    now_str,
    pick_text,
    random_delay,
    str_contains_any,
)


def _extract_token_from_soup(soup: BeautifulSoup, selector: str, attr: str) -> str:
    el = soup.select_one(selector)
    if not el:
        return ""
    if attr == "text":
        return pick_text(el)
    return el.get(attr, "")


def login(client: HttpClient, login_cfg: Dict[str, Any], username: str, password: str) -> bool:
    if not login_cfg:
        return True

    page_path = (login_cfg or {}).get("page_path")
    submit_path = (login_cfg or {}).get("submit_path") or page_path or "/"
    method = ((login_cfg or {}).get("submit_method") or "POST").upper()

    headers = (login_cfg or {}).get("headers") or {}

    fields_cfg = (login_cfg or {}).get("fields") or {}
    username_field = fields_cfg.get("username_field", "username")
    password_field = fields_cfg.get("password_field", "password")
    static_fields = fields_cfg.get("static") or {}

    extract_list: List[Dict[str, str]] = (login_cfg or {}).get("extract") or []

    tokens: Dict[str, str] = {}
    soup = None
    if page_path:
        print(f"[{now_str()}] 打开登录页: {client.url(page_path)}")
        resp, soup = client.fetch_soup(page_path)
        if resp.status_code >= 400:
            print(f"[{now_str()}] 登录页响应异常: {resp.status_code}")
            return False
        for item in extract_list:
            name = item.get("name")
            selector = item.get("selector")
            attr = item.get("attr", "value")
            if name and selector:
                tokens[name] = _extract_token_from_soup(soup, selector, attr)

    payload: Dict[str, str] = {
        username_field: username,
        password_field: password,
        **static_fields,
        **tokens,
    }

    print(f"[{now_str()}] 提交登录: {client.url(submit_path)}")
    if method == "POST":
        resp = client.post(submit_path, data=payload, headers=headers)
    else:
        resp = client.get(submit_path, params=payload, headers=headers)

    soup2 = BeautifulSoup(resp.text, "lxml")

    success_cfg = (login_cfg or {}).get("success") or {}
    failure_cfg = (login_cfg or {}).get("failure") or {}

    ok = True
    if success_cfg.get("css_selector"):
        ok = bool(soup2.select_one(success_cfg.get("css_selector")))
    if ok and success_cfg.get("redirect_path"):
        ok = success_cfg.get("redirect_path") in (resp.url or "")
    if failure_cfg.get("text_contains"):
        if failure_cfg.get("text_contains") in resp.text:
            ok = False

    if ok:
        print(f"[{now_str()}] 登录成功")
    else:
        print(f"[{now_str()}] 登录失败，请检查配置或账号密码")
    return ok


def _parse_course_items(soup: BeautifulSoup, cfg: Dict[str, Any], base_url: str) -> List[Dict[str, str]]:
    item_sel = cfg.get("item_selector")
    parse_cfg = cfg.get("parse") or {}
    items: List[Dict[str, str]] = []
    if not item_sel:
        return items
    for row in soup.select(item_sel):
        item: Dict[str, str] = {}
        for key, rule in parse_cfg.items():
            sel = rule.get("selector")
            attr = rule.get("attr", "text")
            el = row.select_one(sel) if sel else None
            if not el:
                item[key] = ""
                continue
            if attr == "text":
                item[key] = clean_space(el.get_text(" ", strip=True))
            else:
                val = el.get(attr, "")
                if key == "link":
                    val = absolute_url(val, base_url)
                item[key] = val
        items.append(item)
    return items


def _filter_courses(courses: List[Dict[str, str]], filt: Dict[str, Any]) -> List[Dict[str, str]]:
    ids = set(filt.get("ids") or [])
    includes = filt.get("include_keywords") or []
    excludes = filt.get("exclude_keywords") or []

    def want(c: Dict[str, str]) -> bool:
        cid = c.get("id", "")
        name = c.get("name", "")
        if ids and cid in ids:
            return True
        if includes and (str_contains_any(name, includes) or str_contains_any(cid, includes)):
            return True
        if excludes and (str_contains_any(name, excludes) or str_contains_any(cid, excludes)):
            return False
        return bool(includes or ids)

    selected = [c for c in courses if want(c)]
    return selected


def _try_enroll(client: HttpClient, course: Dict[str, str], submit_cfg: Dict[str, Any]) -> bool:
    method = (submit_cfg.get("method") or "GET").upper()
    path = submit_cfg.get("path")
    fields = submit_cfg.get("fields") or {}

    if method == "GET" and not path:
        link = course.get("link")
        if not link:
            print(f"[{now_str()}] 课程 {course.get('id')} 缺少可用链接，跳过")
            return False
        resp = client.get(link)
    else:
        data = {}
        for k, v in fields.items():
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                key = v.strip("{} ")
                data[k] = course.get(key, "")
            else:
                data[k] = str(v)
        resp = client.post(path or "", data=data)

    if resp.status_code >= 400:
        print(f"[{now_str()}] 课程 {course.get('id')} 选课请求失败: {resp.status_code}")
        return False

    return True


def _enroll_success(resp_text: str, success_cfg: Dict[str, Any]) -> bool:
    keywords: List[str] = success_cfg.get("text_contains") or []
    for k in keywords:
        if k and k in resp_text:
            return True
    return not keywords  # 未配置关键字则以请求成功即通过


def run_enroll(client: HttpClient, cfg: Dict[str, Any]) -> None:
    enroll_cfg = cfg.get("site", {}).get("enroll", {})
    if not enroll_cfg or not enroll_cfg.get("enabled", True):
        print(f"[{now_str()}] 选课功能未启用，跳过")
        return

    list_path = enroll_cfg.get("list_path")
    print(f"[{now_str()}] 打开课程列表页: {client.url(list_path)}")
    resp, soup = client.fetch_soup(list_path, method="GET")
    if resp.status_code >= 400:
        print(f"[{now_str()}] 课程列表页请求失败: {resp.status_code}")
        return

    courses = _parse_course_items(soup, enroll_cfg, client.base_url)
    print(f"[{now_str()}] 解析到课程数量: {len(courses)}")

    target_courses = _filter_courses(courses, enroll_cfg.get("filter") or {})
    print(f"[{now_str()}] 目标课程数量: {len(target_courses)}")

    submit_cfg = enroll_cfg.get("submit") or {"method": "GET"}
    success_cfg = enroll_cfg.get("success") or {}

    for idx, course in enumerate(target_courses, 1):
        print(f"[{now_str()}] 尝试选课({idx}/{len(target_courses)}): {course.get('id')} {course.get('name')}")
        ok = _try_enroll(client, course, submit_cfg)
        client.sleep(random_delay())
        if not ok:
            continue
        # 简单检查结果页
        # 若 GET link 方式，上一请求 resp 不在此处；为简化，这里再打开列表页判断
        resp2 = client.get(enroll_cfg.get("list_path"))
        if _enroll_success(resp2.text, success_cfg):
            print(f"[{now_str()}] 课程 {course.get('id')} 选课成功")
        else:
            print(f"[{now_str()}] 课程 {course.get('id')} 可能未成功，请检查页面或调整配置")
