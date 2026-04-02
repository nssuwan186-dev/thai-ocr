# 🇹🇭 Thai OCR with Deep Learning - GitHub Actions

## 🎯 วิธีใช้งาน

### **1. Push รูปขึ้นไป GitHub**

```bash
# เพิ่มรูปในโฟลเดอร์
cp ~/downloads/*.jpg images/

# Commit และ push
git add images/
git commit -m "📷 Add Thai hotel registration images"
git push origin main
```

### **2. GitHub Actions จะรัน OCR อัตโนมัติ**

Workflow จะ:
1. ✅ Checkout repository
2. ✅ Install Python + Deep Learning model (PaddleOCR หรือ EasyOCR)
3. ✅ Scan ทุกรูปด้วย **Thai OCR**
4. ✅ Extract ข้อมูล: ชื่อ, เบอร์, ห้อง, วันที่, การชำระเงิน
5. ✅ บันทึกผลลัพธ์เป็น JSON + CSV
6. ✅ Commit ผลลัพธ์กลับเข้า repo
7. ✅ Upload เป็น artifact (เก็บไว้ 30 วัน)

### **3. ดูผลลัพธ์**

#### **บน GitHub:**
- ไปที่ **Actions** tab
- คลิก workflow ล่าสุด
- ดูผลลัพธ์ใน **Artifacts**

#### **Download ผลลัพธ์:**
```bash
git pull
cat results/ocr-results.json
cat results/ocr-data.csv
```

---

## 📁 โครงสร้างไฟล์

```
hotel-ocr/
├── .github/
│   └── workflows/
│       ├── thai-ocr.yml         # Workflow configuration
│       └── run-thai-ocr.py      # OCR scanner script
├── images/                      # Put images here
├── uploads/                     # Or here
├── drive-downloads/             # Or here
└── results/                     # Auto-generated results
    ├── ocr-results.json
    ├── ocr-data.csv
    └── summary.json
```

---

## 🚀 Manual Trigger

สามารถรัน workflow ด้วยตนเอง:

1. ไปที่ **Actions** tab
2. เลือก **🇹🇭 Thai OCR with Deep Learning**
3. กด **Run workflow**
4. เลือก options:
   - **Model:** paddleocr หรือ easyocr
5. กด **Run workflow**

---

## 📊 ตัวอย่างผลลัพธ์

### **summary.json:**
```json
{
  "total_images": 321,
  "successful": 295,
  "failed": 26,
  "model": "paddleocr",
  "language": "th",
  "average_confidence": 87.5
}
```

### **ocr-data.csv:**
```csv
file,name,phone,id_card,room,checkin,checkout,payment,confidence
"images/0.jpg","สมชาย ใจดี","081-234-5678","1-2345-67890-12-3","B110","02/04/2026","05/04/2026","เงินสด",89.5
```

---

## 🔧 Customization

### **เลือก OCR Model:**

**PaddleOCR** (แนะนำ):
- แม่นยำสูง (90%+)
- รองรับภาษาไทยดี
- เร็ว

**EasyOCR**:
- แม่นยำปานกลาง (85%+)
- ใช้งานง่าย
- ช้ากว่า

### **เปลี่ยนโฟลเดอร์:**

แก้ไฟล์ `thai-ocr.yml`:
```yaml
on:
  push:
    paths:
      - 'my-images/**'  # เปลี่ยนตรงนี้
```

---

## 💡 Tips

### **1. จัดการรูปเป็นโฟลเดอร์:**
```bash
mkdir images/batch-2026-04
cp *.jpg images/batch-2026-04/
git add images/batch-2026-04/
git push
```

### **2. ดู Progress:**
- ไปที่ **Actions** tab
- ดู workflow ที่กำลังรัน
- ดู log แต่ละ step

### **3. Download Artifact:**
- หลัง workflow เสร็จ
- คลิก **ocr-results-{run_id}** artifact
- Download ZIP file

---

## ⚠️ ข้อจำกัด

- **Free tier:** 2,000 minutes/month
- **OCR time:** ~30-60 seconds per image (Deep Learning)
- **Max images:** ~50-100 images per run
- **Model size:** PaddleOCR ~200MB, EasyOCR ~300MB

---

## 🎯 เปรียบเทียบโมเดล

| Model | ความแม่นยำ | ความเร็ว | ขนาด | ไทย |
|-------|------------|----------|------|-----|
| **PaddleOCR** | 90%+ | ⭐⭐⭐ | ใหญ่ | ✅ |
| **EasyOCR** | 85%+ | ⭐⭐ | กลาง | ✅ |
| **Tesseract** | 70%+ | ⭐⭐⭐⭐ | เล็ก | ❌ |

---

## 📈 ตัวอย่างการใช้งาน

### **Batch Scan 321 รูป:**

```bash
# 1. แตกไฟล์ ZIP
unzip 0000.zip -d drive-downloads/

# 2. เพิ่มเข้า git
git add drive-downloads/
git commit -m "📷 Add 321 Thai hotel images"
git push origin main

# 3. รอ workflow รัน (ประมาณ 3-5 ชั่วโมง)
# 4. Download ผลลัพธ์จาก Actions tab
```

---

## ✅ ข้อดี

- ✅ **ฟรี:** 2,000 minutes/month
- ✅ **ไม่ต้องรันบนมือถือ:** รันบน GitHub cloud
- ✅ **อัตโนมัติ:** Push รูป → OCR ทันที
- ✅ **เก็บผลลัพธ์:** บน GitHub repo
- ✅ **Deep Learning:** แม่นยำ 85-90%
- ✅ **ภาษาไทย:** รองรับโดยโมเดล
- ✅ **ไม่ต้องใส่บัตรเครดิต:** Free tier เพียงพอ

---

## 🔗 Resources

- **PaddleOCR:** https://github.com/PaddlePaddle/PaddleOCR
- **EasyOCR:** https://github.com/JaidedAI/EasyOCR
- **GitHub Actions:** https://github.com/features/actions

---

**พร้อมใช้งานแล้ว!** 🎉
