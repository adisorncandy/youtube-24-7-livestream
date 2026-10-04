# 24/7 YouTube Live Streaming via GitHub Actions (Cloud 100% Free)

ระบบสตรีมมิ่งสด 24/7 บนคลาวด์ของ GitHub Actions ฟรี 100% โดยไม่ต้องเปิดคอมพิวเตอร์ที่บ้าน

## 🚀 คุณสมบัติระบบ
- **รันบนคลาวด์ 100%:** ไม่ต้องเปิดคอมพิวเตอร์ทิ้งไว้
- **Auto Self-Dispatch Loop:** มีระบบวนรอบอัตโนมัติก่อนชนขีดจำกัด 6 ชั่วโมง ทำให้ไลฟ์ต่อเนื่อง 24 ชม./7 วัน
- **ความละเอียด 1080p Full HD:** พร้อมระบบ Reconnect อัตโนมัติเมื่อสัญญาณสะดุด
- **รองรับ 5 ช่องพร้อมกัน:**
  - `in.tween` (Midnight Jazz)
  - `in.mellow` (Chill Acoustic)
  - `in.drip` (Lo-Fi Study Beats)
  - `in.flow` (Deep Flow Beats)
  - `in.natural` (Nature & Organic Vibes)

---

## 🛠️ ขั้นตอนการติดตั้งใช้งาน (ง่ายมาก 4 ขั้นตอน)

### ขั้นตอนที่ 1: สร้าง Repository บน GitHub
1. เข้าไปที่ [GitHub.com](https://github.com) แล้วกด **New repository**
2. ตั้งชื่อ เช่น `youtube-24-7-livestream`
3. **สำคัญมาก:** ให้เลือกเป็น **Public** (เพื่อให้ได้สิทธิ์รัน GitHub Actions ฟรีไม่จำกัดชั่วโมง 100%)

---

### ขั้นตอนที่ 2: เพิ่ม Stream Key ใน GitHub Secrets
1. ในหน้า Repository ของคุณ ให้ไปที่เมนู **Settings** -> **Secrets and variables** -> **Actions**
2. กดปุ่ม **New repository secret** แล้วเพิ่มคีย์ดังนี้:
   - `STREAM_KEY_INTWEEN` : `t6j2-jazc-em0t-zub4-e6wf`
   - `STREAM_KEY_INMELLOW` : `fk9k-322g-bskg-rwa5-dq4y`
   - `STREAM_KEY_INDRIP` : `(Stream Key จาก YouTube Studio ของช่อง in.drip)`
   - `STREAM_KEY_INFLOW` : `(Stream Key จาก YouTube Studio ของช่อง in.flow)`
   - `STREAM_KEY_INNATURAL` : `(Stream Key จาก YouTube Studio ของช่อง in.natural)`
   - `GH_PAT_TOKEN` : `(GitHub Personal Access Token สิทธิ์ workflow สำหรับวนลูปอัตโนมัติ)`

---

### ขั้นตอนที่ 3: อัปโหลดโปรเจกต์ขึ้น GitHub
เปิด Terminal ในโฟลเดอร์นี้แล้วรันคำสั่ง:
```bash
git init
git add .
git commit -m "Initial 24/7 Live Stream Setup"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/youtube-24-7-livestream.git
git push -u origin main
```

---

### ขั้นตอนที่ 4: สั่งเริ่มไลฟ์สด
1. ไปที่แท็บ **Actions** บน GitHub ของคุณ
2. เลือกชื่อช่องที่ต้องการ (เช่น `24/7 Live Stream - in.tween`)
3. กดปุ่ม **Run workflow** -> **Run workflow**
4. ระบบจะเริ่มสตรีมขึ้น YouTube ทันที และจะวนรอบตัวเองอัตโนมัติ 24 ชั่วโมงตลอดกาล!
