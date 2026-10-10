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

# วิชาใน blueprint OR_2 ที่อาจารย์แจ้งภายหลังว่า "ไม่ออกสอบ" → ย้ายจากกลุ่มสอบครั้งที่ 2 ไปกลุ่ม "อื่น ๆ"
# (Kit แจ้ง 1 ต.ค. 2569: ศ.นพ.อภิรักษ์ เสนอ Craniomaxillofacial · ศ.นพ.บรรพต ไม่มี Surgery in Neurology)
EXAM2_CUT = {"Craniomaxillofacial & Surgery", "Surgery in Neurology"}

BOARDS = [
    {"id": "exam1", "label": "สอบครั้งที่ 1", "date_label": "ศ. 18 ก.ย. 2569",
     "path": f"{REPO}/slides/exam-18sep/index.html", "urlbase": f"{BASE}/slides/exam-18sep/"},
    {"id": "exam2", "label": "สอบครั้งที่ 2", "date_label": "ศ. 2 ต.ค. 2569",
     "path": f"{REPO}/slides/exam-02oct/index.html", "urlbase": f"{BASE}/slides/exam-02oct/"},
]

# Scheduled lecturer handouts that are not part of either exam board. Keep them
# discoverable in the schedule site's "อื่น ๆ" documents group without changing exam scope.
ADDITIONAL_OTHER_DOCS = [{
    "id": "quality-improvement-project",
    "num": 52,
    "name": "การจัดทำโครงการพัฒนาคุณภาพ",
    "lecturer": "ดร.วรรณวิมล คงสุวรรณ",
    "day": "5 ต.ค.",
    "qrange": "",
    "qcount": "",
    "exam": "other",
    "docs": [{
        "label": "Handout",
        "url": f"{BASE}/slides/other/2026-10-05-quality-improvement-project-handout.pdf",
    }],
    "status": "ok",
}, {
    "id": "non-technical-skills-patient-safety",
    "num": None,
    "name": "Non-technical Skills for Patient Safety",
    "lecturer": "ดร.วรรณวิมล คงสุวรรณ",
    "day": "2 ต.ค.",
    "qrange": "",
    "qcount": "",
    "exam": "other",
    "docs": [{
        "label": "เอกสาร",
        "url": f"{BASE}/slides/exam-02oct/2026-10-02-non-technical-skills-patient-safety.pdf",
    }],
    "status": "ok",
}, {
    "id": "clinical-practice-orientation",
    "num": 53,
    "name": "Orientation การฝึกภาคปฏิบัติ",
    "lecturer": "พว.วริศรา ตุวยานนท์",
    "day": "9 ต.ค.",
    "qrange": "",
    "qcount": "",
    "exam": "other",
    "docs": [{
        "label": "สไลด์",
        "url": f"{BASE}/slides/other/2026-10-09-clinical-practice-orientation.pdf",
    }],
    "status": "ok",
}, {
    "id": "periop-nursing-management",
    "num": 54,
    "name": "หลักการบริหารและจัดการงานการพยาบาล",
    "lecturer": "ดร.วรรณวิมล คงสุวรรณ",
    "day": "9 ต.ค.",
    "qrange": "",
    "qcount": "",
    "exam": "other",
    "docs": [{
        "label": "สไลด์",
        "url": f"{BASE}/slides/other/2026-10-09-periop-nursing-management.pdf",
    }],
    "status": "ok",
}]

ADDITIONAL_SEMINAR_DOCS = [{
    "id": "seminar-group-3",
    "num": 3,
    "name": "สัมมนากลุ่ม 3",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [],
    "status": "pending",
}, {
    "id": "seminar-group-4-c-arm-radiation-safety",
    "num": 4,
    "name": "ความปลอดภัยทางรังสี (C-Arm Radiation Safety)",
    "lecturer": "",
    "day": "7 ต.ค. 2569",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "PDF (Drive)",
        "tracking": "2026-10-07_group-4_c-arm-radiation-safety.pdf",
        "url": "https://drive.google.com/file/d/1C57fqIXyD3Dzum6EePqz8kecjbg8MBme/view",
    }, {
        "label": "สไลด์ออนไลน์",
        "tracking": "group-4-c-arm-radiation-safety-slides",
        "url": "https://kttwatt.github.io/carm-live/slides",
    }],
    "status": "ok",
}, {
    "id": "seminar-group-5-sharps-safety",
    "num": 5,
    "name": "Sharps Safety",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "PDF (Drive)",
        "tracking": "งานสัมมนา กลุ่ม 5 Sharps safety.pdf",
        "url": "https://drive.google.com/file/d/1tl9OyxDkC_WySD_Q_R8gx1CV48ay7T43/view",
    }],
    "status": "ok",
}, {
    "id": "seminar-group-6-supervision-new-graduate-or-nurses",
    "num": 6,
    "name": "รูปแบบการนิเทศงานพยาบาลจบใหม่ในห้องผ่าตัด",
    "lecturer": "",
    "day": "8 ต.ค. 2569",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "PDF (Drive)",
        "tracking": "2026-10-08_group-6_supervision-new-graduate-OR-nurses.pdf",
        "url": "https://drive.google.com/file/d/1gCPSrdfwyVq4y5vw79PQpsVNc0F_iYD2/view",
    }],
    "status": "ok",
}, {
    "id": "seminar-group-6-aorn-page-1",
    "num": 6,
    "name": "ภาพประกอบกลุ่ม 6 · AORN Periop 101 หน้า 1",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "เปิดภาพ",
        "tracking": "AORN-Periop-101-package-page-1.jpeg",
        "url": "https://drive.google.com/file/d/1FahAN2Zoyz_JotS5Oie8mPEZpvA45UFx/view",
    }],
    "status": "ok",
}, {
    "id": "seminar-group-6-aorn-page-2",
    "num": 6,
    "name": "ภาพประกอบกลุ่ม 6 · AORN Periop 101 หน้า 2",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "เปิดภาพ",
        "tracking": "AORN-Periop-101-package-page-2.jpeg",
        "url": "https://drive.google.com/file/d/1TFyrIpcqZIQNBrtMDjDqxhR0u8K-HKYT/view",
    }],
    "status": "ok",
}, {
    "id": "seminar-group-7-surgical-smoke-safety",
    "num": 7,
    "name": "Surgical Smoke Safety Protocols",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "PDF (Drive)",
        "tracking": "กลุ่ม 7 Surgical Smoke Safety Protocols.pptx.pdf",
        "url": "https://drive.google.com/file/d/1aHGwHfnTggPKjlhCB_Gq9PKEs2hMdkrZ/view",
    }],
    "status": "ok",
}, {
    "id": "seminar-group-8",
    "num": 8,
    "name": "สัมมนากลุ่ม 8",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [],
    "status": "pending",
}, {
    "id": "seminar-rsi",
    "num": None,
    "name": "RSI · ยังไม่ระบุกลุ่ม",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "PDF (Drive)",
        "tracking": "RSI.pdf",
        "url": "https://drive.google.com/file/d/1yjDWzd0tHDXz3fUSnn3RwuFdA3OHRnmk/view",
    }],
    "status": "ok",
}, {
    "id": "seminar-anti-fatigue-floor-mat-head-neck-surgery",
    "num": None,
    "name": "บทความประกอบ · Anti-Fatigue Floor Mat in Head & Neck Surgery",
    "lecturer": "",
    "day": "",
    "qrange": "",
    "qcount": "",
    "exam": "seminar",
    "docs": [{
        "label": "PDF (Drive)",
        "tracking": "2025-anti-fatigue-floor-mat-head-neck-surgery.pdf",
        "url": "https://drive.google.com/file/d/166QjfbCG_P74CpL0ElFt_oIKYcZ9b1IA/view",
    }],
    "status": "ok",
}]



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
        docs = re.findall(r'href="([^"#?]+\.pdf)"', block)
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
            "docs": [{"label": "เอกสาร", "url": urlbase + filename} for filename in docs],
            "status": "ok" if docs else "pending",
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
            continue

        # ขอบเขตสอบครั้งที่ 2 ยึด PDF OR_2 ที่ Kit ส่ง (25 วิชา / 134 ข้อ)
        # ห้ามอาศัยช่วงเลขแถวของ board: MEWS (#25) ไม่มีใน blueprint
        with open("exam2-blueprint.json", encoding="utf-8") as f:
            blueprint = json.load(f)
        by_num = {s["num"]: s for s in subs}
        official = []
        for row in blueprint["subjects"]:
            s = by_num.get(row["board_num"])
            if s is None or s["name"] != row["subject"]:
                raise ValueError(f'Blueprint/board mismatch: {row}')
            s["qcount"] = f'{row["questions"]} ข้อ'
            official.append(s)
        if len(official) != len(blueprint["subjects"]) or sum(
            int(s["qcount"].split()[0]) for s in official
        ) != blueprint["total_questions"]:
            raise ValueError("Blueprint totals mismatch")
        # อาจารย์แจ้งภายหลังว่าไม่ออกสอบ → ย้ายออกจากกลุ่มสอบครั้งที่ 2 (ไปอยู่ "อื่น ๆ" ไม่ลบเอกสาร)
        cut = [s for s in official if s["name"] in EXAM2_CUT]
        if {s["name"] for s in cut} != EXAM2_CUT:
            raise ValueError(f'EXAM2_CUT not found on the board: {EXAM2_CUT - {s["name"] for s in cut}}')
        official = [s for s in official if s["name"] not in EXAM2_CUT]
        exam2_questions = sum(int(s["qcount"].split()[0]) for s in official)
        official_nums = {s["num"] for s in official}
        other = [s for s in subs if s["num"] not in official_nums]
        for s in other:
            s["exam"] = "other"
        other.extend(ADDITIONAL_OTHER_DOCS)
        out["exams"].append({
            "id": "exam2", "label": "สอบครั้งที่ 2",
            "date_label": f'ศ. 2 ต.ค. 2569 · {len(official)} วิชา / {exam2_questions} ข้อ'
                          + (f' (ตัด {len(cut)} วิชาที่อาจารย์แจ้งว่าไม่ออกสอบ)' if cut else ''),
            "urlbase": b["urlbase"], "subjects": official,
        })
        out["exams"].append({
            "id": "other", "label": "อื่น ๆ", "date_label": "ยังไม่อยู่ในลิสต์ทางการ — เก็บไว้ดู",
            "urlbase": b["urlbase"], "subjects": other,
        })
    out["exams"].append({
        "id": "seminar", "label": "สัมมนา", "date_label": "รวมเอกสารสัมมนา",
        "urlbase": "https://kttwatt.github.io/carm-live/", "subjects": ADDITIONAL_SEMINAR_DOCS,
    })
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    for e in out["exams"]:
        ok = sum(1 for s in e["subjects"] if s["status"] == "ok")
        unit = "รายการ" if e["id"] == "seminar" else "วิชา"
        print(f'{e["label"]}: {len(e["subjects"])} {unit} · มีเอกสาร {ok} · รอเอกสาร {len(e["subjects"])-ok}')
        for s in e["subjects"][:3]:
            print(f'   - [{s["num"]}] {s["name"]} | {s["lecturer"]} | {s["day"]} | {s["qrange"]} | {len(s["docs"])} doc')
    print("wrote", OUT, os.path.getsize(OUT), "bytes")
    # ตรวจ: เอกสารทุกไฟล์ใน manifest ต้องมีอยู่จริงในเครื่อง
    missing = []
    for e in out["exams"]:
        for s in e["subjects"]:
            for d in s["docs"]:
                if d["url"].startswith(BASE + "/"):
                    local = d["url"].replace(BASE + "/", REPO + "/", 1)
                    if not os.path.exists(local):
                        missing.append(local)
    print("ไฟล์เอกสารที่หาไม่เจอ:", missing if missing else "ไม่มี (ครบทุกไฟล์)")


if __name__ == "__main__":
    main()
