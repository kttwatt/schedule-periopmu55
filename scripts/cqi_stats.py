#!/usr/bin/env python3
"""สถิติการเปิดเอกสาร CQI (รหัสนักศึกษา 6911801-6911848)

อ่าน event จาก GoatCounter ที่หน้าเว็บยิงมา 2 แบบ:
  cqi-code/<รหัส>              = ปลดล็อกด้วยรหัสนี้
  cqi-open/<รหัส>/<ไฟล์>        = เปิดไฟล์จริง

รายงานแยกเป็น 2 ส่วน: [1] ตามรหัสนักศึกษา   [2] ตามไฟล์
ใช้งาน:
  python3 scripts/cqi_stats.py [วันย้อนหลัง]   รายงาน (หักยอดก่อน baseline แล้ว)
  python3 scripts/cqi_stats.py --baseline     จับยอดนับใหม่ (เริ่มนับจากตอนนี้)
"""
import os
import sys
import json
import urllib.request
from datetime import date, timedelta, datetime

SITE = "periopmu55.goatcounter.com"
KEYFILE = os.path.expanduser("~/.config/goatcounter.env")
BASEFILE = os.path.expanduser("~/.config/cqi-stats-baseline.json")
WINDOW_DAYS = 30


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
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "User-Agent": "hermes-agent/1.0",   # GoatCounter ตอบ 404 ถ้า UA เป็น Python-urllib
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def parse(hits):
    """→ unlocks{code:n}, locks{"code/file":n}, legacy{"file":n}"""
    unlocks, locks, legacy = {}, {}, {}
    for h in hits:
        path = h.get("path", "").lstrip("/")
        n = h.get("count", 0)
        if path.startswith("cqi-code/"):
            code = path.split("/", 1)[1].strip("/")
            unlocks[code] = unlocks.get(code, 0) + n
        elif path.startswith("cqi-open/"):
            parts = path.split("/")
            key = f"{parts[1]}/{parts[2]}" if len(parts) >= 3 else f"nocode/{parts[-1]}"
            locks[key] = locks.get(key, 0) + n
        elif path.endswith(".pdf"):
            legacy[path] = legacy.get(path, 0) + n
    return unlocks, locks, legacy


def minus(cur, base):
    out = {}
    for k, v in cur.items():
        rest = v - base.get(k, 0)
        if rest > 0:
            out[k] = rest
    return out


def load_base():
    if os.path.exists(BASEFILE):
        try:
            return json.load(open(BASEFILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def main():
    args = list(sys.argv[1:])
    if "--baseline" in args:
        unlocks, locks, legacy = parse(fetch_hits(WINDOW_DAYS).get("hits", []))
        snap = {"taken_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "unlocks": unlocks, "locks": locks, "legacy": legacy}
        os.makedirs(os.path.dirname(BASEFILE), exist_ok=True)
        json.dump(snap, open(BASEFILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"จับยอดนับใหม่เมื่อ {snap['taken_at']}")
        print(f"ยอดสะสมเดิม (ไม่นับแล้ว): ปลดล็อก {sum(unlocks.values())} ครั้ง · "
              f"เปิดไฟล์ {sum(locks.values())} ครั้ง · ไฟล์เก่า {sum(legacy.values())} ครั้ง")
        print(f"บันทึก baseline ที่ {BASEFILE}")
        return

    days = WINDOW_DAYS
    for a in args:
        if a.isdigit():
            days = int(a)
    start = (date.today() - timedelta(days=days)).isoformat()

    unlocks, locks, legacy = parse(fetch_hits(days).get("hits", []))
    base = load_base()
    if base:
        unlocks = minus(unlocks, base.get("unlocks", {}))
        locks = minus(locks, base.get("locks", {}))
        legacy = minus(legacy, base.get("legacy", {}))

    per_code, per_file = {}, {}
    for key, n in locks.items():
        code, fname = key.split("/", 1)
        per_code.setdefault(code, {})
        per_code[code][fname] = per_code[code].get(fname, 0) + n
        per_file.setdefault(fname, {})
        per_file[fname][code] = per_file[fname].get(code, 0) + n

    total_opens = sum(sum(f.values()) for f in per_code.values())
    tag = f"นับใหม่ตั้งแต่ {base['taken_at']}" if base else f"สะสม {days} วัน (ตั้งแต่ {start})"
    print(f"═══ สถิติเอกสาร CQI · {tag} ═══")
    print(f"รวม: เปิดไฟล์ {total_opens} ครั้ง · {len(per_code)} รหัส · ปลดล็อก {sum(unlocks.values())} ครั้ง\n")

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
        print("\nยังไม่มีข้อมูลในช่วงนี้ — ต้องมีคนเข้าเว็บจริงและกดเปิดไฟล์ (event เข้าระบบภายใน ~1 นาที)")


if __name__ == "__main__":
    main()
