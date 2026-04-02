#!/usr/bin/env python3
"""
Thai Hotel Registration Form OCR - PaddleOCR (Free)
ใช้ PaddleOCR อ่านฟอร์มทะเบียนผู้เข้าพัก
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from paddleocr import PaddleOCR
from PIL import Image
from tqdm import tqdm

# ---- Config ----------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def extract_hotel_data(text):
    """Extract hotel registration data from OCR text"""
    data = {
        'room_number': '-',
        'guest_name': '-',
        'id_card': '-',
        'phone': '-',
        'vehicle_plate': '-',
        'checkin_date': '-',
        'checkin_time': '-',
        'checkout_date': '-',
        'nights': '-',
        'payment_method': '-',
        'source_file': ''
    }
    
    lines = text.split('\n')
    
    # Room number - มองหาตัวเลขที่มีตัวอักษรนำหน้า
    room_match = re.search(r'([A-Z]{1,2}\d{2,4})', text, re.I)
    if room_match:
        data['room_number'] = room_match.group(1)
    
    # Guest name - มองหาภาษาไทยหลัง "ชื่อ"
    for line in lines:
        if 'ชื่อ' in line or 'นามสกุล' in line:
            thai_match = re.search(r'([\u0E00-\u0E7F\s\.]{5,50})', line)
            if thai_match:
                data['guest_name'] = thai_match.group(1).strip()
                break
    
    # Phone
    phone_match = re.search(r'(\d{2,4}[-.\s]?\d{3}[-.\s]?\d{4})', text)
    if phone_match:
        data['phone'] = phone_match.group(1)
    
    # ID Card
    id_match = re.search(r'(\d{1}[-]?\d{4}[-]?\d{5}[-]?\d{2}[-]?\d{1})', text)
    if id_match:
        data['id_card'] = id_match[1]
    
    # Vehicle plate
    vehicle_match = re.search(r'([ก-ฮ]{1,2}\d{3,4})', text)
    if vehicle_match:
        data['vehicle_plate'] = vehicle_match.group(1)
    
    # Dates
    dates = re.findall(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
    if dates:
        data['checkin_date'] = dates[0]
        if len(dates) > 1:
            data['checkout_date'] = dates[1]
    
    # Time
    time_match = re.search(r'(\d{1,2}:\d{2})', text)
    if time_match:
        data['checkin_time'] = time_match.group(1)
    
    # Payment
    if 'เงินสด' in text:
        data['payment_method'] = 'เงินสด'
    elif 'โอน' in text:
        data['payment_method'] = 'โอนเงิน'
    elif 'บัตรเครดิต' in text:
        data['payment_method'] = 'บัตรเครดิต'
    
    return data

def run_ocr(folder, output):
    # Initialize PaddleOCR (Thai language)
    print("🤖 Loading PaddleOCR (Thai)...")
    ocr = PaddleOCR(use_angle_cls=True, lang='th')
    
    image_folder = Path(folder)
    if not image_folder.exists():
        print(f"ERROR: folder '{folder}' not found")
        sys.exit(1)
    
    images = sorted(
        p for p in image_folder.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    
    if not images:
        print(f"No images found in '{folder}'")
        sys.exit(0)
    
    print(f"📂 Found {len(images)} image(s) in '{folder}'")
    
    results = []
    for img_path in tqdm(images, desc="OCR"):
        print(f"  🔍 {img_path.name}...", end=" ", flush=True)
        
        try:
            # Run OCR (new API - without cls parameter)
            result = ocr.ocr(str(img_path))
            
            # Extract text
            text = ''
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text += line[1][0] + '\n'
            
            # Extract hotel data
            hotel_data = extract_hotel_data(text)
            hotel_data['source_file'] = img_path.name
            
            # Add confidence
            confidence = 0.0
            if result and result[0]:
                confidences = [line[1][1] for line in result[0] if line and len(line) >= 2]
                if confidences:
                    confidence = sum(confidences) / len(confidences)
            hotel_data['confidence'] = f"{confidence:.2f}"
            
            results.append(hotel_data)
            
            print(f"✓ ห้อง={hotel_data['room_number']} ชื่อ={hotel_data['guest_name']}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({
                'source_file': img_path.name,
                'error': str(e),
                'confidence': '0.00'
            })
    
    # Save output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"\n💾 Saved {len(results)} record(s) → {output_path}")
    
    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'ห้อง':<10} {'ชื่อ':<25} {'เช็คอิน':<12} {'โทร':<15} {'ความมั่นใจ':<10}")
    print("-" * 80)
    for r in results:
        if 'error' not in r:
            print(
                f"{str(r.get('room_number') or '-'):<10} "
                f"{str(r.get('guest_name') or '-'):<25} "
                f"{str(r.get('checkin_date') or '-'):<12} "
                f"{str(r.get('phone') or '-'):<15} "
                f"{str(r.get('confidence') or '-'):<10}"
            )
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thai Hotel Form OCR - PaddleOCR")
    parser.add_argument("--folder", default="images", help="Image folder path")
    parser.add_argument("--output", default="results/ocr_result.json", help="Output JSON path")
    args = parser.parse_args()
    
    run_ocr(args.folder, args.output)
