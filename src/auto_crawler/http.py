from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup


@dataclass
class HttpClient:
    base_url: str
    session: requests.Session

    @staticmethod
    def create(base_url: str, default_headers: Optional[Dict[str, str]] = None) -> "HttpClient":
        sess = requests.Session()
        sess.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })
        if default_headers:
            sess.headers.update(default_headers)
        return HttpClient(base_url=base_url.rstrip("/"), session=sess)

    def url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not path_or_url.startswith("/"):
            path_or_url = "/" + path_or_url
        return self.base_url + path_or_url

    def get(self, path_or_url: str, **kwargs) -> requests.Response:
        return self.session.get(self.url(path_or_url), **kwargs)

    def post(self, path_or_url: str, data: Dict[str, str], **kwargs) -> requests.Response:
        return self.session.post(self.url(path_or_url), data=data, **kwargs)

    def fetch_soup(self, path_or_url: str, method: str = "GET", **kwargs) -> Tuple[requests.Response, BeautifulSoup]:
        method_u = method.upper()
        if method_u == "GET":
            resp = self.get(path_or_url, **kwargs)
        else:
            resp = self.post(path_or_url, data=kwargs.get("data", {}), **{k: v for k, v in kwargs.items() if k != "data"})
        soup = BeautifulSoup(resp.text, "lxml")
        return resp, soup

    def sleep(self, seconds: float) -> None:
        time.sleep(max(0.0, seconds))
