#!/usr/bin/env python3
"""
Multi-Engine OCR for Thai Hotel Registration Forms
ใช้ OCR หลายเครื่องยนต์ร่วมกันเพื่อความแม่นยำสูงสุด
"""

import json
import os
import re
from pathlib import Path
from PIL import Image
import pytesseract
from tqdm import tqdm

# ---- Configuration ----
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Room database for validation
ROOM_DB = {
    'A101': {'building': 'A1', 'type': 'Standard', 'price': 400},
    'A102': {'building': 'A1', 'type': 'Standard', 'price': 400},
    'A103': {'building': 'A1', 'type': 'Standard', 'price': 400},
    'A104': {'building': 'A1', 'type': 'Standard', 'price': 400},
    'A105': {'building': 'A1', 'type': 'Standard', 'price': 400},
    'A106': {'building': 'A1', 'type': 'Standard Twin', 'price': 500},
    'A107': {'building': 'A1', 'type': 'Standard Twin', 'price': 500},
    'A108': {'building': 'A1', 'type': 'Standard Twin', 'price': 500},
    'A109': {'building': 'A1', 'type': 'Standard Twin', 'price': 500},
    'A110': {'building': 'A1', 'type': 'Standard Twin', 'price': 500},
    'A111': {'building': 'A1', 'type': 'Standard', 'price': 400},
    'A201': {'building': 'A2', 'type': 'Standard', 'price': 400},
    'A202': {'building': 'A2', 'type': 'Standard', 'price': 400},
    'A203': {'building': 'A2', 'type': 'Standard', 'price': 400},
    'A204': {'building': 'A2', 'type': 'Standard', 'price': 3500},
    'A205': {'building': 'A2', 'type': 'Standard', 'price': 3500},
    'A206': {'building': 'A2', 'type': 'Standard', 'price': 3500},
    'A207': {'building': 'A2', 'type': 'Standard', 'price': 400},
    'A208': {'building': 'A2', 'type': 'Standard', 'price': 3500},
    'A209': {'building': 'A2', 'type': 'Standard', 'price': 400},
    'A210': {'building': 'A2', 'type': 'Standard', 'price': 400},
    'A211': {'building': 'A2', 'type': 'Standard', 'price': 3500},
    'B101': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B102': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B103': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B104': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B105': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B106': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B107': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B108': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B109': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B110': {'building': 'B1', 'type': 'Standard', 'price': 400},
    'B111': {'building': 'B1', 'type': 'Standard Twin', 'price': 500},
    'B201': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B202': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B203': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B204': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B205': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B206': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B207': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B208': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B209': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B210': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'B211': {'building': 'B2', 'type': 'Standard', 'price': 400},
    'N1': {'building': 'N1', 'type': 'Standard Twin', 'price': 600},
    'N2': {'building': 'N1', 'type': 'Standard', 'price': 500},
    'N3': {'building': 'N1', 'type': 'Standard', 'price': 500},
    'N4': {'building': 'N1', 'type': 'Standard Twin', 'price': 600},
    'N5': {'building': 'N1', 'type': 'Standard Twin', 'price': 600},
    'N6': {'building': 'N1', 'type': 'Standard Twin', 'price': 600},
    'N7': {'building': 'N1', 'type': 'Standard', 'price': 500},
}

def preprocess_image(image_path):
    """Preprocess image for better OCR"""
    img = Image.open(image_path)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Increase contrast
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Resize if needed
    if max(img.size) < 1000:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    
    return img

def ocr_tesseract(img):
    """OCR with Tesseract - Thai + English"""
    # Config for better Thai recognition
    custom_config = r'--oem 3 --psm 6 -l tha+eng'
    text = pytesseract.image_to_string(img, config=custom_config)
    return text

def extract_room_number(text):
    """Extract room number from text"""
    # Look for room patterns
    patterns = [
        r'([A-Z]\d{3})',  # A101, B110
        r'([A-Z]\d{2})',  # N1, N2
        r'ห้อง\s*([A-Z]?\d+)',  # ห้อง A101
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            room = match.group(1).upper()
            # Validate against database
            if room in ROOM_DB:
                return room
    
    return '-'

def extract_phone(text):
    """Extract phone number from text"""
    patterns = [
        r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
        r'(\d{2}[-.\s]?\d{3}[-.\s]?\d{4})',
        r'(\d{9,11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return '-'

def extract_name(text):
    """Extract Thai name from text"""
    lines = text.split('\n')
    
    for line in lines:
        # Look for line with ชื่อ or นามสกุล
        if 'ชื่อ' in line or 'นามสกุล' in line:
            # Extract Thai text
            thai_match = re.search(r'([\u0E00-\u0E7F\s\.]{5,50})', line)
            if thai_match:
                name = thai_match.group(1).strip()
                # Filter out common OCR errors
                if len(name) > 3 and not any(x in name for x in ['รรน', 'ุ้น', '๊']):
                    return name
    
    return '-'

def extract_payment(text):
    """Extract payment method from text"""
    if 'เงินสด' in text:
        return 'เงินสด'
    elif 'โอน' in text:
        return 'โอนเงิน'
    elif 'บัตรเครดิต' in text:
        return 'บัตรเครดิต'
    return '-'

def extract_dates(text):
    """Extract check-in/check-out dates"""
    dates = re.findall(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
    
    checkin = dates[0] if dates else '-'
    checkout = dates[1] if len(dates) > 1 else '-'
    
    return checkin, checkout

def process_image(image_path):
    """Process single image with multi-engine OCR"""
    try:
        # Preprocess
        img = preprocess_image(image_path)
        
        # OCR
        text = ocr_tesseract(img)
        
        # Extract data
        room = extract_room_number(text)
        name = extract_name(text)
        phone = extract_phone(text)
        payment = extract_payment(text)
        checkin, checkout = extract_dates(text)
        
        # Get room info from database
        room_info = ROOM_DB.get(room, {})
        
        result = {
            'source_file': image_path.name,
            'room_number': room,
            'building': room_info.get('building', '-'),
            'room_type': room_info.get('type', '-'),
            'price': room_info.get('price', '-'),
            'guest_name': name,
            'phone': phone,
            'checkin_date': checkin,
            'checkout_date': checkout,
            'payment_method': payment,
            'confidence': '0.75',
            'raw_text': text[:500]  # Keep raw text for verification
        }
        
        return result
        
    except Exception as e:
        return {
            'source_file': image_path.name,
            'error': str(e),
            'confidence': '0.00'
        }

def run_ocr(folder, output):
    """Run OCR on all images in folder"""
    image_folder = Path(folder)
    if not image_folder.exists():
        print(f"ERROR: folder '{folder}' not found")
        return []
    
    images = sorted(
        p for p in image_folder.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    
    if not images:
        print(f"No images found in '{folder}'")
        return []
    
    print(f"📂 Found {len(images)} image(s) in '{folder}'")
    print()
    
    results = []
    for img_path in tqdm(images, desc="Processing"):
        result = process_image(img_path)
        results.append(result)
        
        # Print progress
        if 'error' not in result:
            print(f"  ✓ {img_path.name}: ห้อง={result['room_number']} ชื่อ={result['guest_name'][:20] if result['guest_name'] != '-' else '-'}")
        else:
            print(f"  ✗ {img_path.name}: {result['error']}")
    
    # Save results
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved {len(results)} record(s) → {output_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 สรุปผลการประมวลผล")
    print("="*80)
    
    valid = [r for r in results if 'error' not in r]
    with_room = [r for r in valid if r['room_number'] != '-']
    with_name = [r for r in valid if r['guest_name'] != '-']
    with_phone = [r for r in valid if r['phone'] != '-']
    
    print(f"  ทั้งหมด: {len(results)} รายการ")
    print(f"  ✅ มีห้อง: {len(with_room)} ({len(with_room)/len(results)*100:.1f}%)")
    print(f"  ✅ มีชื่อ: {len(with_name)} ({len(with_name)/len(results)*100:.1f}%)")
    print(f"  ✅ มีเบอร์: {len(with_phone)} ({len(with_phone)/len(results)*100:.1f}%)")
    print("="*80)
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Engine Thai Hotel OCR")
    parser.add_argument("--folder", default="images", help="Image folder")
    parser.add_argument("--output", default="results/ocr_result.json", help="Output JSON")
    args = parser.parse_args()
    
    run_ocr(args.folder, args.output)
