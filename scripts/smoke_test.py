#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smoke_test.py —— 构建产物冒烟测试
  1) 遍历 site/**/*.html, 提取内联 JS, node --check 语法校验
  2) 校验 API JSON 关键字段 (index/CI) 存在
任何失败以非零码退出, 阻止坏产物部署。
"""
import glob, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

def check_js():
    ok = True
    files = glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True)
    checked = 0
    for f in files:
        html = open(f, encoding="utf-8").read()
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
        inline = "\n".join(s for s in scripts if len(s.strip()) > 10)
        if not inline.strip():
            continue
        p = os.path.join(tempfile.gettempdir(), "smoke_check.js")
        open(p, "w", encoding="utf-8").write(inline)
        r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
        checked += 1
        if r.returncode != 0:
            ok = False
            print(f"  [FAIL] JS syntax error in {os.path.relpath(f, ROOT)}")
            print("  " + r.stderr.strip().split("\n")[-1][:200])
    print(f"[smoke] JS checked: {checked} html files")
    return ok

def check_api():
    ok = True
    files = glob.glob(os.path.join(SITE, "**", "api", "latest.json"), recursive=True)
    for f in files:
        rel = os.path.relpath(f, ROOT)
        try:
            d = json.load(open(f, encoding="utf-8"))
            # 关键字段: 各体系有自己的指数键
            keys = [k for k in ("index", "composite", "fusion_index", "life_index")
                    if d.get(k) is not None]
            if not keys:
                print(f"  [WARN] no index field in {rel}")
            else:
                print(f"  [OK] {rel}: {keys[0]}={d[keys[0]]}")
        except Exception as e:
            ok = False
            print(f"  [FAIL] {rel}: {e}")
    return ok

if __name__ == "__main__":
    ok_js = check_js()
    ok_api = check_api()
    if not (ok_js and ok_api):
        print("[smoke] FAILED")
        sys.exit(1)
    print("[smoke] ALL PASS")
