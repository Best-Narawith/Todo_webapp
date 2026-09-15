# แผนงาน — Todo_webapp

อัปเดตล่าสุด: 2026-09-15 · branch ที่ทำงานอยู่: `main` · **กลุ่ม A, B, C เสร็จครบ · เทส 82 ตัว**

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
  - พฤติกรรมที่เปลี่ยนโดยตั้งใจ: `PATCH`/`DELETE` หา task ก่อนแล้วค่อยตรวจ body → task ที่ไม่มีตอบ **404 ก่อน 400** (เดิมกลับกัน) — มีเทสล็อกแล้ว
- **รอบ 2026-09-14 — เสร็จ 3 ข้อ + ครึ่ง** (`780ad5f` `95dfa7c` `f0fe96e`)
  - เทสล็อก 404-ก่อน-400 ของ `PATCH` (`test_patch_missing_task_returns_404_before_validation`)
  - `username`: `validate_username()` ใน `auth.py` — strip หน้า-หลังเงียบ ๆ · ปัดช่องว่างตรงกลาง · เพดาน 80 (= `String(80)`) · บังคับเฉพาะ `register` · เทส 9 เคสเช็คทั้ง status และว่าลง/ไม่ลง DB
  - blur ในโหมดแก้ = **ยกเลิก** (คืน label เดิม ไม่ยิง GET) — `app.js`
  - save พลาดตอนแก้ข้อความ: เลิก `alert()` → โชว์ `response.json().error` ที่ช่องกรอกด้วย `setCustomValidity` + `reportValidity` (alert ดึงโฟกัส → ยิง blur → ช่องหาย นี่คือเหตุที่ต้องเปลี่ยน) — ลองใน browser แล้ว ใช้ได้
- **กลุ่ม B — เสร็จทั้งกลุ่ม** (2026-09-14/15)
  - `alert()` หมดจาก `app.js` แล้วทุกจุด (`9fa2c82`) — `failureMessage(response, fallback)` จัดการ response ทุกตัวที่เดียว: 401 เด้ง login · error อื่นคืนข้อความจาก backend
    - toggle / delete / load → ข้อความแดงใน `#task-error` ใต้ form · add / แก้ข้อความ → bubble ที่ช่องกรอกผ่าน `reportValidity`
    - toggle / delete ที่พลาด **`await loadTasks()` ก่อนแล้วค่อย `showError`** — ไม่งั้น `loadTasks` จะ `hideError()` ทับข้อความที่เพิ่งโชว์
    - ข้อความหายเองเมื่อโหลดสำเร็จรอบถัดไป หรือเมื่อผู้ใช้เริ่มพิมพ์
    - ตรวจด้วย Chrome จริง (playwright) 8 เคสผ่านหมด
  - หน้า error 404 / 500 (`0b49ede`) — `templates/error_handler.html` ใบเดียวรับ `error` · `@app.errorhandler` ใน `app.py` **ต้องคืน `, 404` / `, 500`** ไม่งั้นได้ 200
    - `/api/*` ไม่กระทบ เพราะ route ตอบ `jsonify(...), 404` เอง ไม่ได้ `abort(404)` → handler ไม่ถูกเรียก (มีเทสล็อกแล้ว)
- เทส: **82 ตัว** เขียวหมด (44 ตอนจบกลุ่ม B → 82 หลังกลุ่ม C)
- ลองแล้วเลิก: redesign frontend เป็น dark minimal — ทำเสร็จบน branch แล้วตัดสินใจคงหน้าเดิม ลบ branch ทิ้ง (mockup ยังอยู่ใน artifact ถ้าอยากกลับมาดู)

---

## งานถัดไป (เรียงตามที่คุยกันไว้)

**กลุ่ม A, B, C — เสร็จหมดแล้ว (2026-09-15)** · เทส 82 ตัว เขียวหมด

> **สิ่งที่เหลือคือหัวข้อใน "อื่น ๆ" ท้ายส่วนนี้** — เลือกได้ตามใจ ไม่มีอะไรค้างที่จำเป็นต้องทำ

**กลุ่ม C — ความปลอดภัย** (เรียงตามความคุ้ม = ผลกระทบ ÷ แรง) — **ปิดครบทั้ง 8 ข้อ**

1. **`debug=True` ตอน production** ([app.py](todo_app/app.py) บรรทัดสุดท้าย) — **ร้ายสุด** ถ้า deploy แล้วลืมปิด หน้า error จะมี interactive console ที่รันโค้ด Python ได้จากเบราว์เซอร์ = ยึดเครื่อง · แก้: อ่านจาก env เหมือน `SECRET_KEY`
2. **`SECRET_KEY` มี default `"dev-only-key"`** ([app.py:9](todo_app/app.py#L9)) — ถ้าลืมตั้ง env ตอน deploy ใครก็รู้ key นี้ (อยู่บน GitHub) → **ปลอม cookie session เป็น user_id ไหนก็ได้** · แก้: ตอน production ถ้าไม่มี env ให้ crash ทันที ดีกว่าเงียบ ๆ ใช้ default
3. **cookie flags** — ตอนนี้ได้แค่ `HttpOnly` (Flask ให้เอง) ขาด `SameSite=Lax` และ `Secure` · แก้ที่ `app.config` 3 บรรทัด ไม่ต้องแตะ route · **กับดัก: `Secure` บน http จะทำให้ login ไม่ติด** ต้องอ่านจาก env (`"1"` เท่านั้น — ค่าใน `os.environ` เป็น string เสมอ `"0"` ก็ truthy)
4. **password ไม่มีขั้นต่ำ/เพดาน** ([auth.py](todo_app/auth.py)) — `"b"` ตัวเดียวก็สมัครได้
   > **แก้ข้อมูลเดิม (วัดจริง 2026-09-15):** ที่เคยเขียนว่า "ยาวมาก ๆ ทำให้ `generate_password_hash` กิน CPU = DoS" **ไม่จริง** — werkzeug ใช้ scrypt (`32768:8:1`) ต้นทุนมาจากพารามิเตอร์ที่ตายตัว ไม่ขึ้นกับความยาว input: 8 ตัว = 67 ms · 1,000,000 ตัว = 71 ms · hash ที่เก็บยาว 162 ตัวเสมอ → คอลัมน์ `String(255)` ไม่เคยเป็นปัญหา
   > และ Werkzeug ปฏิเสธ form ที่ใหญ่เกิน ~500 KB ด้วย **413** อยู่แล้วก่อนถึงโค้ดเรา (ทดสอบ: 400,000 ตัว → 302 · 500,000 ตัว → 413)
   > **DoS จริงคือต้นทุนคงที่ 67 ms/ครั้ง** ไม่ว่ารหัสสั้นยาว → ทางแก้คือ rate limit (ข้อ 6) ไม่ใช่จำกัดความยาว
   > เพดานยังควรมี แต่เหตุผลคือ error ที่อ่านรู้เรื่อง (413 เปล่า ๆ ไม่บอกอะไร) ไม่ใช่ CPU
   > **กฎของ password ที่ต่างจาก `detail`:** ห้าม `.strip()` ห้ามตัดให้สั้นลง — ต้อง **ปฏิเสธ** อย่างเดียว เพราะดัดแปลงแล้วผู้ใช้จะ login ไม่ได้ตลอดกาลโดยไม่รู้สาเหตุ (กับดักคลาสสิก: bcrypt ตัดที่ 72 bytes เงียบ ๆ — scrypt ที่เราใช้ไม่มีปัญหานี้)
5. CSRF token บนฟอร์ม login/register
6. ~~rate limit หน้า login~~ — **เสร็จ 2026-09-15** เขียนเอง (ไม่ใช้ library) ใน [auth.py](todo_app/auth.py) นับ 2 แกนพร้อมกัน: ต่อ IP (20 ครั้ง/5 นาที กัน password spraying) · ต่อ username (5 ครั้ง/5 นาที กัน brute-force จาก botnet) · login สำเร็จล้างประวัติ · ตอบ `429` · เช็ก**ก่อน** `check_password_hash` ไม่งั้นยังเสีย CPU 67 ms ต่อครั้ง · 6 เทส
   > **ข้อจำกัดที่รู้อยู่ ยังไม่แก้:**
   > 1. **เก็บในหน่วยความจำ** (`auth._failed_logins`) — restart แล้วหาย · รันหลาย process แต่ละตัวนับแยกกัน → ของจริงต้องใช้ Redis
   > 2. **account lockout DoS** — ยิงรหัสผิดใส่ `somchai` 5 ครั้งทุก 5 นาที = `somchai` login ไม่ได้ตลอด · แก้จริงต้องซับซ้อนกว่านี้ (เช่นบล็อกเฉพาะ IP ที่ไม่เคยเห็น หรือหน่วงเวลาแทนบล็อก)
   > 3. **`request.remote_addr` เชื่อไม่ได้เมื่ออยู่หลัง proxy** — จะได้ IP ของ proxy เหมือนกันหมดทุกคน → ต้องอ่าน `X-Forwarded-For` แต่ header นั้นปลอมได้ ต้องตั้ง `ProxyFix` ให้เชื่อเฉพาะ proxy ของเรา
   >
   > เทสต้องล้าง `auth._failed_logins` ใน fixture `client` เพราะ state อยู่ใน module ไม่ใช่ DB · ฟังก์ชันรับ `now=None` เพื่อให้เทสส่งเวลาปลอมได้ ไม่ต้องรอ 5 นาทีจริง (หลักเดียวกับ `resolve_secret_key` ที่รับ `env_var`)
7. ~~`PRAGMA foreign_keys = ON`~~ — **เสร็จ 2026-09-15** ใส่กลับใน [model.py](todo_app/model.py) ด้วย `@event.listens_for(Engine, "connect")` เพราะ PRAGMA มีผลแค่ connection เดียว ต้องสั่งใหม่ทุกครั้งที่เปิด · มี `isinstance(dbapi_connection, sqlite3.Connection)` กันไว้เผื่อย้ายไป PostgreSQL ที่ไม่รู้จัก PRAGMA นี้ · 3 เทส
   > **พิสูจน์แล้วว่าทำไมสำคัญ** (ยิงจริงก่อนแก้): ลบ user ที่มี task → task กลายเป็นแถวกำพร้าชี้ไป `user_id` ที่ไม่มีอยู่ · แล้ว **คนที่สมัครใหม่ได้ id เดิม (SQLite แจก `max(id)+1`) จะเห็นงานของคนเก่าทั้งหมด** = ข้อมูลรั่วข้ามบัญชี ไม่มี error ใด ๆ เตือน
   >
   > **พฤติกรรมที่เปลี่ยน:** `db.session.delete(user)` ที่ยังมี task ค้าง ตอนนี้ raise `IntegrityError` แทนที่จะลบเงียบ ๆ · ยังไม่กระทบเพราะยังไม่มีฟีเจอร์ลบบัญชี — วันที่ทำต้องเลือก `cascade="all, delete-orphan"` (ลบ task ตาม) หรือห้ามลบบัญชีที่ยังมีงาน
   >
   > เทสที่คาด `IntegrityError` ต้อง `db.session.rollback()` หลัง `pytest.raises` เสมอ ไม่งั้น session ค้างสถานะพังทำให้เทสถัดไปพังตาม
8. ~~`validate_username` จับแค่ space ธรรมดา~~ — **เสร็จ 2026-09-15** เปลี่ยนเป็น **allowlist** `USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")` แทน blocklist ที่แผนเดิมเสนอ (`any(c.isspace() ...)`)
   > **ทำไม allowlist:** blocklist ต้องนึกห้ามให้ครบ ซึ่งทำไม่ได้ — `.strip()` เก็บ tab/newline/non-breaking space ให้แล้ว แต่ **zero-width space (`​`) ไม่ใช่ whitespace ในสายตา Python** จึงหลุดทั้ง strip และ `isspace()` · พิสูจน์แล้วว่า `'somchai'` กับ `'somchai​'` หน้าจอเห็นเหมือนกันเป๊ะแต่ `==` เป็น False → สมัครชื่อที่ดูเหมือนคนอื่นได้ ไม่ชน UNIQUE
   > **ตัดสินใจ: ASCII เท่านั้น ไม่รับภาษาไทย** — เพราะ `\w` แบบ UNICODE ปล่อย fullwidth latin (`ｓｏｍｃｈａｉ`) ผ่าน ซึ่งเป็นปัญหา homograph · แนวเดียวกับ GitHub/Twitter ที่แยก username (ต้องไม่กำกวม) ออกจาก display name (สวยงามได้) — ถ้าอยากได้ชื่อไทยให้ทำ display name เป็นฟีเจอร์แยก
   > เช็กความยาว**ก่อน** pattern ไม่งั้นชื่อยาวที่มีอักขระแปลกจะได้ error ผิดเรื่อง · `-` ต้องอยู่ท้ายสุดใน `[...]` ไม่งั้นกลายเป็นช่วง
   > เทสมีเคส `thai` คาด 200 ไว้ **ตรึงการตัดสินใจนี้** — วันหลังใครเปลี่ยนใจจะเห็นเทสนี้แดงก่อน

> **XSS — ปลอดภัยอยู่แล้ว** ✅ สแกนแล้ว `app.js` ใช้ `textContent` กับ `detail` ทุกที่ (ไม่ใช่ `innerHTML`) และ template ไม่ได้ render ข้อมูล user → พิมพ์ `<script>` ในงานก็ไม่ทำงาน
>
> **พิสูจน์แล้วว่าทำไม cookie สำคัญ:** เอา cookie string ของเหยื่อไปแปะใน header `Cookie` ของ client ที่ไม่เคย login → อ่าน/ลบงานเหยื่อได้ทันทีโดยไม่ต้องรู้ password · ตอนนี้รันบน http ค่านั้นวิ่งเป็นตัวหนังสือธรรมดา — นี่คือเหตุผลของข้อ 3

**อื่น ๆ**
- Alembic สำหรับ migration (จะได้เพิ่มคอลัมน์ `created_at` โดยไม่ต้องลบ `todo.db`)
- ศัพท์อังกฤษด่าน 4-7 + งานรอบนี้ ลง `english-vocab\WORDBANK.md` (ค้างนาน)

---

## บทเรียนจากรอบ SQLAlchemy (เก็บไว้เตือนตัวเอง)

- **validate ให้จบก่อนค่อย mutate** — ถ้าแก้ `task.done` ไปแล้วค่อยพบว่า `detail` ผิด ค่าที่แก้ค้างอยู่ใน session รอดเพราะ Flask-SQLAlchemy rollback ให้ตอนจบ request ไม่ใช่เพราะออกแบบ
- `except IntegrityError` ต้อง `db.session.rollback()` เสมอ ไม่งั้น request ถัดไปพัง
- `Task.query` / `db.session` นอก request ต้องอยู่ใน `with app.app_context():` (fixture, script)
- **`alert()` ดึงโฟกัส** → ยิง `blur` บน input ที่โฟกัสอยู่ → handler ของ blur รัน*หลัง* alert ปิด flag อะไรก็กันไม่ทัน ทางแก้คือไม่ใช้ alert ในจุดที่มี input โฟกัสอยู่
- `removeEventListener` ต้องส่ง**ฟังก์ชันตัวเดียวกัน** (reference) กับตอน add — `function(){}` เขียนใหม่ = คนละตัว ลบไม่ได้และไม่ error
- เทสต้อง "แดงได้" — ถ้า input ที่ใช้ทำให้ทั้งโค้ดเก่าและใหม่ตอบเหมือนกัน เทสนั้นไม่ได้ล็อกอะไร (พิสูจน์ด้วย `git stash` ไฟล์ที่แก้แล้วรันเทส ต้องแดง)
- แก้ static file แล้ว browser เห็นของเก่า = cache → Ctrl+Shift+R หรือติ๊ก Disable cache ใน DevTools
- **JS: `window.location.href = x` ไม่ใช่ `exit()`** — เป็นการ "ขอให้เปลี่ยนหน้า" โค้ดหลังจากนั้นวิ่งต่อจนกว่า browser จะ unload จริง ฟังก์ชันที่ redirect ต้อง**คืนค่าที่ทำให้ผู้เรียกหยุดด้วย** ไม่ใช่แค่หยุดตัวเอง
- **ลำดับของ `showError` กับ `loadTasks`** — ถ้าอยากโชว์ข้อความแล้วรีเฟรชรายการด้วย ต้อง `await loadTasks()` **ก่อน** `showError()` เพราะ `loadTasks` มี `hideError()` อยู่ข้างใน
- `@app.errorhandler` ไม่ถูกเรียกเมื่อ route `return jsonify(...), 404` เอง (นั่นคือ response ปกติที่บังเอิญเป็น 404) — ถูกเรียกเฉพาะตอน Flask หา route ไม่เจอ หรือโค้ด `abort(404)` · และ handler 500 ถูกข้ามตอน `debug=True` โดยตั้งใจ (ให้ traceback แทน) ต้องทดสอบด้วย `PROPAGATE_EXCEPTIONS = False`
- venv บน Windows ฝัง path absolute — ย้าย folder แล้วต้องสร้างใหม่ (`python -m pytest` ยังรอด แต่ `pytest.exe` / `pip.exe` ตาย)

---

## สำหรับ Claude Code (ทั้งสองเครื่อง)

memory และ `CLAUDE.md` ไม่ตามข้ามเครื่อง บอกมันตอนเริ่มว่า:

- โปรเจกต์นี้เป็น **โหมดโค้ช** — ใบ้ ชี้จุดผิดพร้อมเลขบรรทัด ยิงทดสอบให้ดู แต่**ไม่เขียนโค้ดแทน** ยกเว้นขอตรง ๆ
- ตอบสั้น ตอบไทย คงศัพท์เทคนิคอังกฤษ
- งาน git / ลง package / ยิงทดสอบ / ลบ comment ขยะ ทำให้ได้เลย
- **ก่อนลงมือทุกงาน ถามคำถามออกแบบก่อน** — เช่น "แอปจะรู้ได้ยังไงว่าเป็น production?" ให้เจ้าของตอบเอง แล้วค่อยชี้ข้อดี-ข้อเสียของคำตอบ ไม่ใช่บอกทางแก้เลย (ตกลงกัน 2026-09-15)
- เจ้าของใช้ **Copilot completion** ได้ — เกณฑ์คือ **ต้องอธิบายโค้ดที่ถูกเติมได้ว่าทำอะไร/ทำไม** ถ้าส่งโค้ดมาให้ดู ถามกลับก่อนบอกว่าถูกหรือผิด · ระวัง Copilot เติมของที่ "ดูถูกแต่ไม่จำเป็น" (เช่น fixture ที่ไม่ได้ใช้) หรือผิดกฎโปรเจกต์ (validate ก่อน mutate · `"key" in data` แทน `.get()` · `rollback()` ใน except)
- อ่าน `PLAN.md` นี้ก่อนเริ่ม

ถ้าจะให้ถาวร: สร้าง `CLAUDE.md` ใน repo แล้วย้ายกฎพวกนี้ไปไว้ในนั้น จะโหลดเองทุกเครื่อง
