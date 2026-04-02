#!/usr/bin/env python3
"""
🇹🇭 Thai OCR with Deep Learning
Run on GitHub Actions with PaddleOCR or EasyOCR
"""

import argparse
import json
import os
import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# OCR models
try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

def extract_hotel_data(text):
    """Extract hotel registration data from Thai text"""
    data = {
        'name': '-',
        'phone': '-',
        'room': '-',
        'checkin': '-',
        'checkout': '-',
        'payment': '-',
        'id_card': '-'
    }
    
    lines = text.split('\n')
    
    # Name - Thai text after ชื่อ
    for line in lines:
        if 'ชื่อ' in line or 'นามสกุล' in line:
            thai_match = re.search(r'([\u0E00-\u0E7F\s\.]{5,50})', line)
            if thai_match:
                data['name'] = thai_match.group(1).strip()
                break
    
    # Phone
    phone_match = re.search(r'(\d{2,4}[-.\s]?\d{3}[-.\s]?\d{4})', text)
    if phone_match:
        data['phone'] = phone_match.group(1)
    
    # ID Card
    id_match = re.search(r'(\d{1}[-]?\d{4}[-]?\d{5}[-]?\d{2}[-]?\d{1})', text)
    if id_match:
        data['id_card'] = id_match[1]
    
    # Room
    room_match = re.search(r'ห้อง\s*([A-Z]?[\u0E00-\u0E7F]?\d{2,4})', text, re.I)
    if room_match:
        data['room'] = room_match.group(1).strip()
    
    # Dates
    dates = re.findall(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
    if dates:
        data['checkin'] = dates[0]
        if len(dates) > 1:
            data['checkout'] = dates[1]
    
    # Payment
    if 'เงินสด' in text:
        data['payment'] = 'เงินสด'
    elif 'โอน' in text:
        data['payment'] = 'โอนเงิน'
    elif 'บัตรเครดิต' in text:
        data['payment'] = 'บัตรเครดิต'
    
    return data

def run_paddleocr(image_path, lang='th'):
    """Run PaddleOCR on image"""
    if not HAS_PADDLE:
        return "", 0
    
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        result = ocr.ocr(image_path, cls=True)
        
        text = ''
        confidence = 0
        count = 0
        
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text += line[1][0] + '\n'
                    confidence += line[1][1]
                    count += 1
        
        if count > 0:
            confidence /= count
        
        return text, confidence * 100
    
    except Exception as e:
        print(f"❌ PaddleOCR error: {e}")
        return "", 0

def run_easyocr(image_path, lang=['th', 'en']):
    """Run EasyOCR on image"""
    if not HAS_EASYOCR:
        return "", 0
    
    try:
        reader = easyocr.Reader(lang, gpu=False)
        result = reader.readtext(image_path)
        
        text = ''
        confidence = 0
        
        for (bbox, text_part, conf) in result:
            text += text_part + ' '
            confidence += conf
        
        if len(result) > 0:
            confidence /= len(result)
        
        return text, confidence * 100
    
    except Exception as e:
        print(f"❌ EasyOCR error: {e}")
        return "", 0

def scan_image(image_path, model='paddleocr'):
    """Scan single image with specified model"""
    print(f"🔍 Scanning: {image_path}")
    
    if model == 'easyocr':
        text, confidence = run_easyocr(image_path)
    else:
        text, confidence = run_paddleocr(image_path)
    
    if not text:
        print(f"⚠️  No text detected")
        return None
    
    # Extract hotel data
    extracted = extract_hotel_data(text)
    
    print(f"✅ Confidence: {confidence:.1f}%")
    print(f"📊 Extracted: {json.dumps(extracted, ensure_ascii=False)}")
    
    return {
        'file': str(image_path),
        'ocr_text': text[:1000],
        'confidence': confidence,
        'extracted': extracted,
        'model': model,
        'timestamp': datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser(description='🇹🇭 Thai OCR with Deep Learning')
    parser.add_argument('--input-dir', required=True, help='Input directory with images')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    parser.add_argument('--model', default='paddleocr', choices=['paddleocr', 'easyocr'])
    parser.add_argument('--lang', default='th', help='Language code')
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     🇹🇭 Thai OCR with Deep Learning                     ║")
    print(f"║     Model: {args.model.upper():<45} ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find all images
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(Path(args.input_dir).glob(f'**/*{ext}'))
    
    print(f"📂 Found {len(image_files)} images in {args.input_dir}")
    print()
    
    # Scan all images
    results = []
    
    for image_file in tqdm(image_files, desc="Scanning"):
        result = scan_image(image_file, args.model)
        if result:
            results.append(result)
    
    # Save results
    print()
    print("💾 Saving results...")
    
    # JSON
    with open(os.path.join(args.output_dir, 'ocr-results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # CSV
    import csv
    with open(os.path.join(args.output_dir, 'ocr-data.csv'), 'w', encoding='utf-8', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=['file', 'name', 'phone', 'id_card', 'room', 'checkin', 'checkout', 'payment', 'confidence', 'model'])
            writer.writeheader()
            for r in results:
                row = {
                    'file': r['file'],
                    'name': r['extracted']['name'],
                    'phone': r['extracted']['phone'],
                    'id_card': r['extracted']['id_card'],
                    'room': r['extracted']['room'],
                    'checkin': r['extracted']['checkin'],
                    'checkout': r['extracted']['checkout'],
                    'payment': r['extracted']['payment'],
                    'confidence': r['confidence'],
                    'model': r['model']
                }
                writer.writerow(row)
    
    # Summary
    summary = {
        'total_images': len(image_files),
        'successful': len(results),
        'failed': len(image_files) - len(results),
        'model': args.model,
        'language': args.lang,
        'timestamp': datetime.now().isoformat(),
        'average_confidence': sum(r['confidence'] for r in results) / len(results) if results else 0
    }
    
    with open(os.path.join(args.output_dir, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     ✅ Complete!                                        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"   Total images: {len(image_files)}")
    print(f"   Successful: {len(results)}")
    print(f"   Failed: {len(image_files) - len(results)}")
    print(f"   Average confidence: {summary['average_confidence']:.1f}%")
    print()
    print(f"💾 Results saved to:")
    print(f"   - {args.output_dir}/ocr-results.json")
    print(f"   - {args.output_dir}/ocr-data.csv")
    print(f"   - {args.output_dir}/summary.json")
    print()

if __name__ == '__main__':
    main()
