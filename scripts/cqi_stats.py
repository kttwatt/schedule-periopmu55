#!/usr/bin/env python3
"""สถิติการเปิดเอกสาร CQI (รหัสนักศึกษา 6911801-6911848)

อ่าน event จาก GoatCounter ที่หน้าเว็บยิงมา 2 แบบ:
  cqi-code/<รหัส>              = ปลดล็อกด้วยรหัสนี้
  cqi-open/<รหัส>/<ไฟล์>        = เปิดไฟล์จริง

รายงานแยกเป็น 2 ส่วน: [1] ตามรหัสนักศึกษา   [2] ตามไฟล์
ใช้งาน:  python3 scripts/cqi_stats.py [วันย้อนหลัง]   (ค่าเริ่มต้น 30)
"""
import os
import sys
import json
import urllib.request
from datetime import date, timedelta

SITE = "periopmu55.goatcounter.com"
KEYFILE = os.path.expanduser("~/.config/goatcounter.env")


def load_key():
    key = os.environ.get("GC_KEY", "")
    if not key and os.path.exists(KEYFILE):
        for line in open(KEYFILE, encoding="utf-8"):
            line = line.strip()
            if line.startswith("GC_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def fetch_hits(days):
    key = load_key()
    if not key:
        raise SystemExit("ไม่พบ GC_KEY (ตั้งใน ~/.config/goatcounter.env)")
    start = (date.today() - timedelta(days=days)).isoformat()
    url = f"https://{SITE}/api/v0/stats/hits?start={start}&limit=200&daily=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    start = (date.today() - timedelta(days=days)).isoformat()
    hits = fetch_hits(days).get("hits", [])

    unlocks = {}   # รหัส -> จำนวนครั้งที่ปลดล็อก
    per_code = {}  # รหัส -> {ไฟล์: จำนวนครั้ง}
    per_file = {}  # ไฟล์ -> {รหัส: จำนวนครั้ง}
    legacy = {}    # ไฟล์ -> จำนวนครั้ง (เปิดตอนยังไม่มีระบบรหัส)

    for h in hits:
        path = h.get("path", "").lstrip("/")
        n = h.get("count", 0)
        if path.startswith("cqi-code/"):
            code = path.split("/", 1)[1].strip("/")
            unlocks[code] = unlocks.get(code, 0) + n
        elif path.startswith("cqi-open/"):
            parts = path.split("/")
            if len(parts) >= 3:
                code, fname = parts[1], "/".join(parts[2:])
            else:
                code, fname = "nocode", parts[-1]
            per_code.setdefault(code, {})
            per_code[code][fname] = per_code[code].get(fname, 0) + n
            per_file.setdefault(fname, {})
            per_file[fname][code] = per_file[fname].get(code, 0) + n
        elif path.endswith(".pdf"):
            legacy[path] = legacy.get(path, 0) + n

    total_opens = sum(sum(f.values()) for f in per_code.values())
    print(f"═══ สถิติเอกสาร CQI · {days} วัน (ตั้งแต่ {start}) ═══")
    print(f"รวม: เปิดไฟล์ {total_opens} ครั้ง · {len(per_code)} รหัส · ปลดล็อก {sum(unlocks.values())} ครั้ง\n")

    # ── [1] ตามรหัส
    print("[1] ตามรหัสนักศึกษา")
    if not per_code and not unlocks:
        print("    — ยังไม่มีข้อมูล")
    for code in sorted(set(per_code) | set(unlocks),
                       key=lambda c: (-sum(per_code.get(c, {}).values()), c)):
        files = per_code.get(code, {})
        print(f"    {code}: เปิด {sum(files.values())} ครั้ง · {len(files)} ไฟล์ · ปลดล็อก {unlocks.get(code, 0)} ครั้ง")
        for fname, n in sorted(files.items(), key=lambda kv: -kv[1]):
            print(f"        - {fname} × {n}")
    idle = [c for c in unlocks if c not in per_code]
    if idle:
        print(f"    (ปลดล็อกแต่ยังไม่เปิดไฟล์: {', '.join(idle)})")

    # ── [2] ตามไฟล์
    print("\n[2] ตามไฟล์")
    if not per_file:
        print("    — ยังไม่มีข้อมูล")
    for fname in sorted(per_file, key=lambda f: -sum(per_file[f].values())):
        who = per_file[fname]
        print(f"    {fname}: เปิด {sum(who.values())} ครั้ง · {len(who)} รหัส")
        for code, n in sorted(who.items(), key=lambda kv: -kv[1]):
            print(f"        - {code} × {n}")

    if legacy:
        print("\n(ข้อมูลเก่าก่อนมีระบบรหัส — ไม่รู้ว่าใครเปิด)")
        for fname, n in sorted(legacy.items(), key=lambda kv: -kv[1]):
            print(f"    {fname}: {n} ครั้ง")

    if not (per_code or unlocks or legacy):
        print("\nยังไม่มีข้อมูล — ต้องมีคนเข้าเว็บจริงและกดเปิดไฟล์ (event เข้าระบบภายใน ~1 นาที)")


if __name__ == "__main__":
    main()
