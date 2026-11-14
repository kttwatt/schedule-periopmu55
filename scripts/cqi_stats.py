#!/usr/bin/env python3
"""สถิติการเปิดเอกสาร CQI (รหัสนักศึกษา 6911801-6911848)

อ่าน event จาก GoatCounter ที่หน้าเว็บยิงมา 2 แบบ:
  cqi-code/<รหัส>              = ปลดล็อกด้วยรหัสนี้
  cqi-open/<รหัส>/<ไฟล์>        = เปิดไฟล์จริง

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
    data = fetch_hits(days)
    hits = data.get("hits", [])

    codes = {}     # รหัส -> จำนวนครั้งที่ปลดล็อก
    opens = {}     # รหัส -> {ไฟล์: จำนวน}
    per_file = {}  # ไฟล์ -> {รหัส...}
    untagged = 0

    for h in hits:
        path = h.get("path", "")
        n = h.get("count", 0)
        if path.startswith("cqi-code/"):
            code = path.split("/", 1)[1].strip("/")
            codes[code] = codes.get(code, 0) + n
        elif path.startswith("cqi-open/"):
            parts = path.split("/")
            if len(parts) >= 3:
                code, fname = parts[1], "/".join(parts[2:])
            else:
                code, fname = "nocode", parts[-1]
            opens.setdefault(code, {})
            opens[code][fname] = opens[code].get(fname, 0) + n
            per_file.setdefault(fname, set()).add(code)
        else:
            untagged += n

    total_opens = sum(sum(v.values()) for v in opens.values())
    print(f"สถิติเอกสาร CQI · {days} วันล่าสุด (ตั้งแต่ {(date.today() - timedelta(days=days)).isoformat()})")
    print(f"เปิดเอกสารทั้งหมด: {total_opens} ครั้ง · จากรหัส {len(opens)} คน · ปลดล็อก {sum(codes.values())} ครั้ง\n")

    if not opens and not codes:
        print("ยังไม่มีข้อมูล — ต้องมีคนเข้าเว็บจริงและกดเปิดไฟล์ (event จะเข้าระบบภายใน ~1 นาที)")
        return

    print("รายคน (เรียงตามจำนวนเปิด):")
    for code, files in sorted(opens.items(), key=lambda kv: -sum(kv[1].values())):
        kinds = len(files)
        print(f"  {code}: {sum(files.values())} ครั้ง · {kinds} ไฟล์ · ปลดล็อก {codes.get(code, 0)} ครั้ง")
    missing = sorted({c for c in codes} - {c for c in opens})
    if missing:
        print(f"  (ปลดล็อกแต่ยังไม่เปิดไฟล์: {', '.join(missing)})")

    print("\nรายไฟล์:")
    for fname, who in sorted(per_file.items(), key=lambda kv: -len(kv[1])):
        print(f"  {fname}: {len(who)} คน")

    if untagged:
        print(f"\n(มี event อื่นในระบบ {untagged} ครั้ง — ไม่เกี่ยวกับ CQI)")


if __name__ == "__main__":
    main()
