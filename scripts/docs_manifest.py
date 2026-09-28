#!/usr/bin/env python3
"""สร้าง docs.json (manifest เอกสารรายวิชา) จากหน้า board สไลด์ทั้ง 2 ครั้ง

แหล่งข้อมูล:
  - ~/notes/pykhr627/periop-mu55/slides/exam-18sep/index.html  (สอบครั้งที่ 1)
  - ~/notes/pykhr627/periop-mu55/slides/exam-02oct/index.html  (สอบครั้งที่ 2)
  - ~/notes/pykhr627/schedule.md                                (เอกสารเรียน/วันสอน — ถ้ามี)
ผลลัพธ์: ~/schedule-html/docs.json  (ใช้โดย build_html.py)
"""
import json, re, os, html, datetime

REPO = "/home/kttwatt/notes/pykhr627/periop-mu55"
BASE = "https://kttwatt.github.io/periop-mu55"
OUT = "/home/kttwatt/schedule-html/docs.json"

BOARDS = [
    {"id": "exam1", "label": "สอบครั้งที่ 1", "date_label": "ศ. 18 ก.ย. 2569",
     "path": f"{REPO}/slides/exam-18sep/index.html", "urlbase": f"{BASE}/slides/exam-18sep/"},
    {"id": "exam2", "label": "สอบครั้งที่ 2", "date_label": "ศ. 2 ต.ค. 2569",
     "path": f"{REPO}/slides/exam-02oct/index.html", "urlbase": f"{BASE}/slides/exam-02oct/"},
]


def slug(text, prefix):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    if not s:                     # ชื่อไทยล้วน → ใช้ prefix + เลขลำดับ
        s = prefix
    return s[:48]


def parse_board(path, urlbase, exam_id):
    h = open(path, encoding="utf-8").read()
    # เดินตามเอกสาร: day-header แล้วตามด้วยชุด <li class="row ...">
    tokens = []
    for m in re.finditer(r'<div class="day-header">(.*?)</div>|<li class="row([^"]*)">(.*?)</li>', h, re.S):
        if m.group(1) is not None:
            day = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            tokens.append(("day", day))
        else:
            tokens.append(("row", (m.group(2), m.group(3))))

    subjects, cur_day = [], ""
    for kind, val in tokens:
        if kind == "day":
            cur_day = val
            continue
        cls, block = val
        num = re.search(r'<span class="num">(\d+)</span>', block)
        subj = re.search(r'<span class="subject">(.*?)</span>', block, re.S)
        lect = re.search(r'<span class="lecturer">(.*?)</span>', block, re.S)
        qr = re.search(r'<span class="qrange">(.*?)</span>', block, re.S)
        qc = re.search(r'<span class="qcount">(.*?)</span>', block, re.S)
        doc = re.search(r'href="([^"]+\.pdf)"', block)
        name = html.unescape(re.sub(r'<[^>]+>', '', subj.group(1))).strip() if subj else ""
        lecturer = html.unescape(re.sub(r'<[^>]+>', '', lect.group(1))).strip() if lect else ""
        # ตัดข้อความ qrange ที่ติดมากับ lecturer ออก (เผื่อ parser อื่นแทรก)
        if qr:
            lecturer = lecturer.replace(html.unescape(re.sub(r'<[^>]+>', '', qr.group(1))), "").strip()
        sid = slug(name, f"{exam_id}-{num.group(1) if num else 'x'}")
        item = {
            "id": sid,
            "num": int(num.group(1)) if num else None,
            "name": name,
            "lecturer": lecturer,
            "day": cur_day,
            "qrange": html.unescape(re.sub(r'<[^>]+>', '', qr.group(1))).strip() if qr else "",
            "qcount": html.unescape(re.sub(r'<[^>]+>', '', qc.group(1))).strip() if qc else "",
            "exam": exam_id,
            "docs": ([{"label": "เอกสาร", "url": urlbase + doc.group(1)}] if doc else []),
            "status": "ok" if doc else "pending",
        }
        subjects.append(item)
    return subjects


def main():
    out = {"generated": datetime.date.today().isoformat(), "exams": []}
    for b in BOARDS:
        subs = parse_board(b["path"], b["urlbase"], b["id"])
        # ครั้งที่ 1: ตัด Thoracic ที่เลื่อนไปสอบครั้งที่ 2 (ปรากฏใน board ครั้งที่ 1 ด้วย)
        if b["id"] == "exam1":
            subs = [s for s in subs if "thoracic" not in s["name"].lower()]
        out["exams"].append({
            "id": b["id"], "label": b["label"], "date_label": b["date_label"],
            "urlbase": b["urlbase"], "subjects": subs,
        })
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    for e in out["exams"]:
        ok = sum(1 for s in e["subjects"] if s["status"] == "ok")
        print(f'{e["label"]}: {len(e["subjects"])} วิชา · มีเอกสาร {ok} · รอเอกสาร {len(e["subjects"])-ok}')
        for s in e["subjects"][:3]:
            print(f'   - [{s["num"]}] {s["name"]} | {s["lecturer"]} | {s["day"]} | {s["qrange"]} | {len(s["docs"])} doc')
    print("wrote", OUT, os.path.getsize(OUT), "bytes")
    # ตรวจ: เอกสารทุกไฟล์ใน manifest ต้องมีอยู่จริงในเครื่อง
    missing = []
    for e in out["exams"]:
        for s in e["subjects"]:
            for d in s["docs"]:
                local = d["url"].replace("https://kttwatt.github.io/periop-mu55/", REPO + "/")
                if not os.path.exists(local):
                    missing.append(local)
    print("ไฟล์เอกสารที่หาไม่เจอ:", missing if missing else "ไม่มี (ครบทุกไฟล์)")


if __name__ == "__main__":
    main()
