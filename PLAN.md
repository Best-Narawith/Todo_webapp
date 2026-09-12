# แผนงาน — Todo_webapp

อัปเดตล่าสุด: 2026-09-12 · branch ที่ทำงานอยู่: `sqlalchemy`

---

## ทุกครั้งที่เริ่มทำงาน (ทั้งสองเครื่อง)

```powershell
git status                 # ต้องว่าง — ถ้ามีของค้าง แปลว่าลืม commit ครั้งก่อน
git switch sqlalchemy
git pull
cd todo_app
python -m pytest -q        # ต้องเขียว ถ้าแดงแปลว่ามีอะไรผิดตั้งแต่ก่อนเริ่ม
```

## ทุกครั้งที่เลิกทำงาน

```powershell
python -m pytest -q        # เขียว
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
- Blueprint (`auth.py` / `tasks.py`) — เสร็จ อยู่บน `main`
- **SQLAlchemy — กำลังทำ** บน branch `sqlalchemy`
  - `model.py` เสร็จ (`User`, `Task`) ตารางตรงกับ `schema.sql` เดิม
  - `app.py` ต่อสาย `db.init_app` + `create_all` แล้ว
  - **route ทั้งหมดยังใช้ SQL ดิบผ่าน `database.py` อยู่** ← งานที่เหลือ
- เทส: 31 ตัว เขียวหมด — ห้ามแก้ `test_app.py` ตลอดการย้าย ถ้าต้องแก้แปลว่าพฤติกรรมเปลี่ยน ซึ่งไม่ควรเกิด

---

## งานที่เหลือของ SQLAlchemy — ทำทีละข้อ รันเทสหลังทุกข้อ

ในทุก route: ลบ `conn = database.get_connection()` / `try` / `finally: conn.close()` ออกทั้งก้อน
SQLAlchemy จัดการ connection ให้เอง ใช้ `db.session` แทน

### 4. `GET /api/tasks` — `tasks.py:65-73`
```
เดิม:  SELECT id,detail,done FROM todo_list WHERE user_id=? ORDER BY id ASC
ใหม่:  Task.query.filter_by(user_id=user_id).order_by(Task.id).all()
```
- ได้ list ของ `Task` object ต้องแปลงเป็น dict เองก่อน `jsonify`
  → `[{"id": t.id, "detail": t.detail, "done": t.done} for t in tasks]`
- `t.done` เป็น bool อยู่แล้ว ไม่ต้อง `bool()` ครอบ
- ต้อง `from model import db, Task` บนหัวไฟล์

### 5. `POST /api/tasks` — `tasks.py:57-63`
```
ใหม่:  task = Task(detail=detail, user_id=user_id)
       db.session.add(task)
       db.session.commit()
       → task.id มีค่าหลัง commit ใช้แทน c.lastrowid
```

### 6. `DELETE /api/tasks/<id>` — `tasks.py:84-93`
```
ใหม่:  task = Task.query.filter_by(id=task_id, user_id=user_id).first()
       if task is None: → 404          (แทน rowcount == 0)
       db.session.delete(task)
       db.session.commit()
```

### 7. `PATCH /api/tasks/<id>` — `tasks.py:96-110`
- หา task ด้วย `filter_by(...).first()` → `None` = 404
- ตรวจ `data` เหมือนเดิม (มี key ไหม · `done` เป็น bool ไหม · `detail` ผ่าน `validate_detail` ไหม)
- ถ้ามี `done` → `task.done = data["done"]` · ถ้ามี `detail` → `task.detail = detail`
- `db.session.commit()` — SQLAlchemy คิดเองว่าต้อง UPDATE คอลัมน์ไหน
- ส่งกลับ `{"id": task.id, "detail": task.detail, "done": task.done}` — ไม่ต้อง SELECT ซ้ำแล้ว
- **`build_sql_script` จะไม่มีที่ใช้ → ลบทิ้ง** (`tasks.py:17-35`) แต่ตรรกะตรวจสอบข้างในต้องย้ายมาอยู่ใน route
- เทส `test_patch_*` ทั้ง 11 ตัวคือตัวคุมว่าไม่พลาด

### 8. `auth.py` — `login` (บรรทัด 15-25) และ `register` (บรรทัด 43-53)
```
login:     user = User.query.filter_by(username=username).first()
           if user and check_password_hash(user.password_hash, password): ...
register:  user = User(username=username, password_hash=hashed_password)
           db.session.add(user)
           try: db.session.commit()
           except IntegrityError: db.session.rollback() → "ชื่อนี้ถูกใช้แล้ว"
```
- `IntegrityError` ต้อง import จาก `sqlalchemy.exc` ไม่ใช่ `sqlite3` แล้ว
- **ต้อง `rollback()` ใน except** ไม่งั้น session ค้างสถานะพัง request ถัดไปจะ error ต่อ

### 9. ปิดงาน
- `test_app.py` fixture: เปลี่ยน `DELETE FROM` ดิบ (บรรทัด 15) เป็น
  `Task.query.delete(); User.query.delete(); db.session.commit()` ภายใต้ `app.app_context()`
  และเปลี่ยนวิธีชี้ DB จาก `database.DB_PATH = ...` เป็น `os.environ["DATABASE_URL"] = "sqlite:///<path ชั่วคราว>"` ก่อน import app
  (นี่คือจุดเดียวที่แก้เทสได้ เพราะเป็นโครงสร้าง ไม่ใช่พฤติกรรม)
- `app.py:10` ค่าสำรองของ URI ตอนนี้พึ่ง `database.DB_PATH` → เปลี่ยนเป็น path ที่สร้างเองจาก `Path(__file__).parent / "todo.db"`
- ลบ `database.py` · `schema.sql` · `import database` ทุกที่
- 31 เขียว → commit → `git switch main` → `git merge sqlalchemy` → push
- ลบ branch: `git branch -d sqlalchemy`

---

## หลัง SQLAlchemy เสร็จ (เรียงตามที่คุยกันไว้)

**กลุ่ม B — ฟีเจอร์**
- หน้า error 404 / 500 (`@app.errorhandler`)
- flash message แทน `alert()` ใน `app.js` — และแสดงข้อความ error จริงจาก backend (`response.json().error`) แทนข้อความกลาง ๆ
- blur ตอนอยู่ในโหมดแก้ข้อความ (ตอนนี้ค้างจนกด Enter/Esc)

**กลุ่ม C — ความปลอดภัย** (จำเป็นตอนจะเปิดสู่เน็ตจริง)
- เพดานความยาว `username` (ตอนนี้ 5,000 ตัวก็ผ่าน)
- CSRF token · cookie flags (`Secure`, `HttpOnly`, `SameSite`) · rate limit หน้า login
- `PRAGMA foreign_keys = ON` หายไปตอนย้ายมา SQLAlchemy — ยังไม่มีอะไรพึ่ง แต่ควรใส่กลับด้วย event listener

**อื่น ๆ**
- Alembic สำหรับ migration (จะได้เพิ่มคอลัมน์ `created_at` โดยไม่ต้องลบ `todo.db`)
- ศัพท์อังกฤษด่าน 4-7 + งานรอบนี้ ลง `english-vocab\WORDBANK.md` (ค้างนาน)

---

## สำหรับ Claude Code ที่บ้าน

memory และ `CLAUDE.md` ของเครื่องที่ทำงานไม่ตามมา บอกมันตอนเริ่มว่า:

- โปรเจกต์นี้เป็น **โหมดโค้ช** — ใบ้ ชี้จุดผิดพร้อมเลขบรรทัด ยิงทดสอบให้ดู แต่**ไม่เขียนโค้ดแทน** ยกเว้นขอตรง ๆ
- ตอบสั้น ตอบไทย คงศัพท์เทคนิคอังกฤษ
- งาน git / ลง package / ยิงทดสอบ ทำให้ได้เลย
- อ่าน `PLAN.md` นี้ก่อนเริ่ม

ถ้าจะให้ถาวร: สร้าง `CLAUDE.md` ใน repo แล้วย้ายกฎพวกนี้ไปไว้ในนั้น จะโหลดเองทุกเครื่อง
