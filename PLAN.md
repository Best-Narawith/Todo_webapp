# แผนงาน — Todo_webapp

อัปเดตล่าสุด: 2026-09-13 · branch ที่ทำงานอยู่: `main`

> โครงสร้าง repo เปลี่ยน (2026-09-13): ย้าย project ออกจาก folder ซ้อน — root ของ repo คือ `todo_app_from_home\` โดยตรง
> (`PLAN.md`, `requirements.txt`, `.venv\` อยู่ที่ root · โค้ดอยู่ใน `todo_app\`)
> เครื่องที่ทำงาน: `git pull` แล้วเช็คว่า path ที่ใช้อยู่ตรงกัน ถ้า venv เดิมพัง (ย้าย folder แล้ว venv ใช้ไม่ได้) ให้ลบแล้วสร้างใหม่

> **⚠️ history ของ `main` ถูก rewrite (2026-09-13)** — ลบบรรทัด `Co-Authored-By: Claude` ออกจาก commit message ทุกตัว hash เปลี่ยนหมดตั้งแต่ `bf9afdb` ลงมา
> **เครื่องที่ทำงาน ครั้งแรกหลังจากนี้ห้าม `git pull`** (จะ conflict) ให้รันแทน — ต้องมี `git status` ว่างก่อน ถ้ามีของค้าง `git stash` ไว้:
> ```powershell
> git fetch origin
> git reset --hard origin/main
> ```
> และตั้งค่า Claude Code ที่โน้นให้เหมือนเครื่องนี้ ไม่งั้นบรรทัดนี้จะกลับมาอีก: ใน `~/.claude/settings.json` เพิ่ม `"attribution": {"commit": "", "pr": ""}`

---

## ทุกครั้งที่เริ่มทำงาน (ทั้งสองเครื่อง)

```powershell
git status                 # ต้องว่าง — ถ้ามีของค้าง แปลว่าลืม commit ครั้งก่อน
git switch main
git pull
.venv\Scripts\Activate.ps1 # prompt ต้องขึ้น (.venv) — ถ้าไม่มี .venv: python -m venv .venv แล้ว pip install -r requirements.txt
cd todo_app
pytest -q                  # ต้องเขียว ถ้าแดงแปลว่ามีอะไรผิดตั้งแต่ก่อนเริ่ม
```

## ทุกครั้งที่เลิกทำงาน

```powershell
pytest -q                  # เขียว
git add <ไฟล์ที่แก้>         # ทีละไฟล์ ไม่ใช้ git add .
git diff --staged          # เช็คก่อนกด (q ออกจาก pager)
git commit -m "..."
git push
```

ถ้าเลิกกลางคัน commit เป็น `WIP: ...` แล้วบอกในข้อความว่าค้างตรงไหน

---

## สถานะตอนนี้

- กลุ่ม A (บั๊ก 5 ข้อ) — เสร็จ
- ฟีเจอร์แก้ข้อความงาน (backend + frontend) — เสร็จ
- Blueprint (`auth.py` / `tasks.py`) — เสร็จ
- **SQLAlchemy — เสร็จ** merge เข้า `main` แล้ว (`f788802`, 2026-09-13)
  - `database.py` · `schema.sql` ลบแล้ว ไม่มีที่ไหนอ้างถึงอีก
  - DB ชี้ผ่าน `DATABASE_URL` env · ค่าสำรองคือ `todo_app/todo.db` (คำนวณจาก `Path(__file__)` ใน `app.py`)
  - เทสชี้ temp DB ด้วย `os.environ["DATABASE_URL"]` ก่อน `from app import app` และล้างตารางผ่าน `db.session` ใน `app.app_context()`
  - พฤติกรรมที่เปลี่ยนโดยตั้งใจ: `PATCH`/`DELETE` หา task ก่อนแล้วค่อยตรวจ body → task ที่ไม่มีตอบ **404 ก่อน 400** (เดิมกลับกัน) เทสไม่ครอบเคสนี้
  - ค้าง: `git push origin --delete sqlalchemy` (branch บน remote ยังอยู่ ลบจากเครื่องไหนก็ได้)
- เทส: 31 ตัว เขียวหมด

---

## งานถัดไป (เรียงตามที่คุยกันไว้)

**กลุ่ม B — ฟีเจอร์**
- หน้า error 404 / 500 (`@app.errorhandler`)
- flash message แทน `alert()` ใน `app.js` — และแสดงข้อความ error จริงจาก backend (`response.json().error`) แทนข้อความกลาง ๆ
- blur ตอนอยู่ในโหมดแก้ข้อความ (ตอนนี้ค้างจนกด Enter/Esc)

**กลุ่ม C — ความปลอดภัย** (จำเป็นตอนจะเปิดสู่เน็ตจริง)
- เพดานความยาว `username` (ตอนนี้ 5,000 ตัวก็ผ่าน — `model.py` ประกาศ `String(80)` แต่ SQLite ไม่บังคับ ต้องเช็คเองใน `register`)
- CSRF token · cookie flags (`Secure`, `HttpOnly`, `SameSite`) · rate limit หน้า login
- `PRAGMA foreign_keys = ON` หายไปตอนย้ายมา SQLAlchemy — ยังไม่มีอะไรพึ่ง แต่ควรใส่กลับด้วย event listener (`sqlalchemy.event.listens_for(Engine, "connect")`)

**อื่น ๆ**
- Alembic สำหรับ migration (จะได้เพิ่มคอลัมน์ `created_at` โดยไม่ต้องลบ `todo.db`)
- เทสเคส `PATCH` task ที่ไม่มี + body เพี้ยน → ล็อกพฤติกรรม 404 ที่เปลี่ยนไปข้างบน
- ศัพท์อังกฤษด่าน 4-7 + งานรอบนี้ ลง `english-vocab\WORDBANK.md` (ค้างนาน)

---

## บทเรียนจากรอบ SQLAlchemy (เก็บไว้เตือนตัวเอง)

- **validate ให้จบก่อนค่อย mutate** — ถ้าแก้ `task.done` ไปแล้วค่อยพบว่า `detail` ผิด ค่าที่แก้ค้างอยู่ใน session รอดเพราะ Flask-SQLAlchemy rollback ให้ตอนจบ request ไม่ใช่เพราะออกแบบ
- `except IntegrityError` ต้อง `db.session.rollback()` เสมอ ไม่งั้น request ถัดไปพัง
- `Task.query` / `db.session` นอก request ต้องอยู่ใน `with app.app_context():` (fixture, script)
- venv บน Windows ฝัง path absolute — ย้าย folder แล้วต้องสร้างใหม่ (`python -m pytest` ยังรอด แต่ `pytest.exe` / `pip.exe` ตาย)

---

## สำหรับ Claude Code (ทั้งสองเครื่อง)

memory และ `CLAUDE.md` ไม่ตามข้ามเครื่อง บอกมันตอนเริ่มว่า:

- โปรเจกต์นี้เป็น **โหมดโค้ช** — ใบ้ ชี้จุดผิดพร้อมเลขบรรทัด ยิงทดสอบให้ดู แต่**ไม่เขียนโค้ดแทน** ยกเว้นขอตรง ๆ
- ตอบสั้น ตอบไทย คงศัพท์เทคนิคอังกฤษ
- งาน git / ลง package / ยิงทดสอบ / ลบ comment ขยะ ทำให้ได้เลย
- อ่าน `PLAN.md` นี้ก่อนเริ่ม

ถ้าจะให้ถาวร: สร้าง `CLAUDE.md` ใน repo แล้วย้ายกฎพวกนี้ไปไว้ในนั้น จะโหลดเองทุกเครื่อง
