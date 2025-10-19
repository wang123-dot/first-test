from __future__ import annotations

import argparse
import sys

from .auto_enroll import login, run_enroll
from .auto_evaluate import run_evaluate
from .config import AppConfig
from .http import HttpClient
from .utils import now_str, random_delay, ts_until


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="自动选课与评教（通用可配置）")
    parser.add_argument("--config", "-c", default="config.yaml", help="配置文件路径，默认 config.yaml")
    parser.add_argument("--mode", choices=["enroll", "evaluate", "both"], default="both")
    parser.add_argument("--at", help="在指定时间点开始执行，格式 YYYY-MM-DD HH:MM:SS，可用于抢课")
    args = parser.parse_args(argv)

    cfg = AppConfig.load(args.config).data

    # 等待到指定时间
    if args.at:
        wait_sec = ts_until(args.at)
        if wait_sec > 0:
            print(f"[{now_str()}] 等待至 {args.at} 开始（约 {wait_sec:.1f}s）...")
            import time

            time.sleep(wait_sec)

    base_url = (cfg.get("site", {}) or {}).get("base_url", "").rstrip("/")
    if not base_url:
        print("缺少 site.base_url 配置")
        return 2

    client = HttpClient.create(base_url)

    # 登录
    username = (cfg.get("credentials") or {}).get("username")
    password = (cfg.get("credentials") or {}).get("password")
    if not username or not password:
        print("缺少 credentials.username/password 配置")
        return 2

    if not login(client, (cfg.get("site") or {}).get("login", {}), username, password):
        return 1

    # 执行
    if args.mode in ("enroll", "both"):
        run_enroll(client, cfg)

    if args.mode in ("evaluate", "both"):
        run_evaluate(client, cfg)

    # 轻微延迟后退出
    import time

    time.sleep(random_delay(0.1, 0.3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
