#!/usr/bin/env python3
"""
Thai Hotel Registration Form OCR
ใช้ Claude Vision API อ่านฟอร์มทะเบียนผู้เข้าพัก Vipat Bungkan Hotel
แล้วดึงข้อมูลออกมาเป็น JSON
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import anthropic
from PIL import Image

# ---- config ----------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

SYSTEM_PROMPT = """คุณคือระบบ OCR สำหรับอ่านฟอร์ม "ทะเบียนผู้เข้าพัก" ของโรงแรม Vipat Bungkan Hotel
ให้อ่านข้อมูลจากรูปภาพและตอบกลับเป็น JSON เท่านั้น ห้ามมีข้อความอื่นนอกจาก JSON

โครงสร้าง JSON ที่ต้องการ:
{
  "room_number": "เลขห้อง เช่น B116, N3, B110",
  "guest_name": "ชื่อ-นามสกุล (ถ้าอ่านไม่ออกให้ใส่ null)",
  "id_card": "เลขบัตรประชาชน (ถ้าไม่มีให้ใส่ null)",
  "phone": "เบอร์โทร (ถ้าไม่มีให้ใส่ null)",
  "vehicle_plate": "ทะเบียนรถ (ถ้าไม่มีให้ใส่ null)",
  "checkin_date": "วันที่เช็คอิน เช่น 14-3-69",
  "checkin_time": "เวลาเช็คอิน เช่น 19:30",
  "checkout_date": "วันที่เช็คเอ้าท์ (ถ้าไม่มีให้ใส่ null)",
  "nights": "จำนวนคืน (ตัวเลขจำนวนเต็ม ถ้าไม่มีให้ใส่ null)",
  "room_type": "ประเภทเตียง: เดี่ยว หรือ คู่ (ถ้าไม่ระบุให้ใส่ null)",
  "building_type": "ประเภทห้อง: ตึก/อาคาร หรือ บ้านน็อคดาวน์ (ถ้าไม่ระบุให้ใส่ null)",
  "room_rate": "ราคาห้องต่อคืน (ตัวเลข ถ้าไม่มีให้ใส่ null)",
  "extra_charges": "รายการเพิ่มเติม (ถ้าไม่มีให้ใส่ null)",
  "total_amount": "ยอดชำระรวม (ตัวเลข ถ้าไม่มีให้ใส่ null)",
  "payment_method": "วิธีชำระ: เงินสด หรือ โอนบัญชี (ถ้าไม่ระบุให้ใส่ null)",
  "note": "หมายเหตุมุมกระดาษหรือข้อมูลอื่นที่เห็น (ถ้าไม่มีให้ใส่ null)",
  "confidence": "ความมั่นใจในการอ่าน 0.0-1.0"
}

กฎสำคัญ:
- ถ้าอ่านตัวเลขหรือตัวอักษรไม่ชัดเจน ให้ใส่ค่าที่อ่านได้ใกล้เคียงที่สุด
- ห้ามเดาข้อมูลที่ไม่เห็นในภาพ
- ตอบกลับเป็น JSON เท่านั้น ไม่มีคำอธิบาย"""

USER_PROMPT = """อ่านฟอร์มทะเบียนผู้เข้าพักในรูปภาพนี้และดึงข้อมูลทั้งหมดออกมาเป็น JSON"""

# ---- helpers ---------------------------------------------------------------

def encode_image(image_path: Path) -> tuple[str, str]:
    """Encode image to base64 and return (base64_data, media_type)."""
    suffix = image_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")

    # Resize if too large (Claude max ~5MB per image)
    with Image.open(image_path) as img:
        if max(img.size) > 3000:
            img.thumbnail((3000, 3000), Image.LANCZOS)
            import io
            buf = io.BytesIO()
            fmt = "JPEG" if suffix in (".jpg", ".jpeg") else "PNG"
            img.save(buf, format=fmt)
            data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
        else:
            data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    return data, media_type


def ocr_single_image(client: anthropic.Anthropic, image_path: Path) -> dict:
    """Run OCR on a single image and return parsed dict."""
    print(f"  OCR: {image_path.name} ...", end=" ", flush=True)

    b64_data, media_type = encode_image(image_path)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    },
                    {"type": "text", "text": USER_PROMPT},
                ],
            }
        ],
    )

    raw_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        raw_text = raw_text.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw_text)
        result["source_file"] = image_path.name
        print(f"✓ room={result.get('room_number')} name={result.get('guest_name')}")
    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error: {e}")
        result = {
            "source_file": image_path.name,
            "error": f"JSON parse error: {e}",
            "raw": raw_text,
        }

    return result


def run_ocr(folder: str, output: str) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    image_folder = Path(folder)
    if not image_folder.exists():
        print(f"ERROR: folder '{folder}' not found", file=sys.stderr)
        sys.exit(1)

    images = sorted(
        p for p in image_folder.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not images:
        print(f"No images found in '{folder}'")
        sys.exit(0)

    print(f"Found {len(images)} image(s) in '{folder}'")

    results = []
    for img_path in images:
        result = ocr_single_image(client, img_path)
        results.append(result)

    # Save output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved {len(results)} record(s) → {output_path}")

    # Print summary table
    print("\n" + "=" * 60)
    print(f"{'ห้อง':<8} {'ชื่อ':<20} {'เช็คอิน':<12} {'โทร':<15}")
    print("-" * 60)
    for r in results:
        if "error" not in r:
            print(
                f"{str(r.get('room_number') or '-'):<8} "
                f"{str(r.get('guest_name') or '-'):<20} "
                f"{str(r.get('checkin_date') or '-'):<12} "
                f"{str(r.get('phone') or '-'):<15}"
            )
    print("=" * 60)


# ---- main ------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thai Hotel Form OCR")
    parser.add_argument("--folder", default="images", help="Image folder path")
    parser.add_argument("--output", default="results/ocr_result.json", help="Output JSON path")
    args = parser.parse_args()

    run_ocr(args.folder, args.output)
