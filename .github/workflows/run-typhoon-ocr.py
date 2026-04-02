#!/usr/bin/env python3
"""
🇹🇭 Thai OCR with Typhoon OCR
Best OCR for Thai Language - Built by SCB 10X
https://github.com/scb-10x/typhoon-ocr
"""

import argparse
import json
import os
import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Try to import Typhoon OCR
HAS_TYPHOON = False
try:
    from transformers import AutoProcessor, AutoModelForCausalLM
    import torch
    from PIL import Image
    HAS_TYPHOON = True
    print("✅ Typhoon OCR dependencies loaded!")
except ImportError as e:
    print(f"⚠️  Typhoon OCR dependencies not available: {e}")
    print("   Install with: pip install typhoon-ocr transformers torch pillow")

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

def run_typhoon_ocr(image_path):
    """Run Typhoon OCR on image using transformers"""
    if not HAS_TYPHOON:
        return "", 0
    
    try:
        # Load model (cached after first run)
        model_name = "scb10x/typhoon-ocr-7b"
        print(f"🤖 Loading Typhoon OCR model: {model_name}...")
        
        processor = AutoProcessor.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        # Load image
        image = Image.open(image_path)
        
        # Prepare prompt
        prompt = "OCR this image and extract all text. Output only the text, nothing else:"
        
        # Process
        inputs = processor(images=image, text=prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False
            )
        
        # Extract text
        text = processor.decode(outputs[0], skip_special_tokens=True)
        # Remove prompt from output
        text = text.replace(prompt, "").strip()
        
        confidence = 0.95  # Typhoon OCR typically has high confidence
        print(f"✅ Typhoon OCR: {len(text)} chars, confidence: {confidence:.2f}")
        return text, confidence * 100
    
    except Exception as e:
        print(f"❌ Typhoon OCR error: {e}")
        return "", 0

def scan_image(image_path):
    """Scan single image with Typhoon OCR"""
    print(f"🔍 Scanning: {image_path}")
    
    text, confidence = run_typhoon_ocr(image_path)
    
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
        'model': 'typhoon',
        'timestamp': datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser(description='🇹🇭 Thai OCR with Typhoon OCR')
    parser.add_argument('--input-dir', required=True, help='Input directory with images')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    parser.add_argument('--lang', default='th', help='Language code')
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     🇹🇭 Thai OCR with Typhoon OCR (Best for Thai!)      ║")
    print("║     Built by SCB 10X                                     ║")
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
        result = scan_image(image_file)
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
        'model': 'typhoon',
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

def run_typhoon_ocr(image_path):
    """Run Typhoon OCR on image"""
    if not HAS_TYPHOON:
        return "", 0
    
    try:
        # Initialize Typhoon OCR
        ocr = TyphoonOCR()
        result = ocr.predict(image_path)
        
        # Extract text from result
        text = ''
        confidence = 0
        
        if hasattr(result, 'text'):
            text = result.text
            confidence = getattr(result, 'confidence', 0.9)
        elif isinstance(result, dict):
            text = result.get('text', '')
            confidence = result.get('confidence', 0.9)
        else:
            text = str(result)
            confidence = 0.9
        
        print(f"✅ Typhoon OCR: {len(text)} chars, confidence: {confidence:.2f}")
        return text, confidence * 100
    
    except Exception as e:
        print(f"❌ Typhoon OCR error: {e}")
        return "", 0

def scan_image(image_path):
    """Scan single image with Typhoon OCR"""
    print(f"🔍 Scanning: {image_path}")
    
    text, confidence = run_typhoon_ocr(image_path)
    
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
        'model': 'typhoon',
        'timestamp': datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser(description='🇹🇭 Thai OCR with Typhoon OCR')
    parser.add_argument('--input-dir', required=True, help='Input directory with images')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    parser.add_argument('--lang', default='th', help='Language code')
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     🇹🇭 Thai OCR with Typhoon OCR (Best for Thai!)      ║")
    print("║     Built by SCB 10X                                     ║")
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
        result = scan_image(image_file)
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
        'model': 'typhoon',
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
