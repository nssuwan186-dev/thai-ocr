#!/usr/bin/env python3
"""
Validate and Correct OCR Results using Room Database
ตรวจสอบและแก้ไขผลลัพธ์ OCR โดยใช้ฐานข้อมูลห้อง
"""

import json
from pathlib import Path

def load_room_database():
    """Load room database"""
    db_path = Path('room_database.json')
    if db_path.exists():
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_ocr_results():
    """Load OCR results"""
    result_path = Path('results/ocr_result.json')
    if result_path.exists():
        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def validate_room_number(room_db, ocr_room):
    """Validate and correct room number"""
    if not ocr_room or ocr_room == '-':
        return None
    
    # Try exact match
    for room in room_db:
        if room['room_number'] == ocr_room:
            return room['room_number']
    
    # Try fuzzy match (extract numbers)
    import re
    ocr_nums = re.findall(r'\d+', ocr_room)
    if ocr_nums:
        for room in room_db:
            db_nums = re.findall(r'\d+', room['room_number'])
            if db_nums and ocr_nums[0] == db_nums[0]:
                # Check building prefix
                if ocr_room[0].upper() == room['room_number'][0].upper():
                    return room['room_number']
    
    return None

def validate_and_correct(ocr_results, room_db):
    """Validate and correct OCR results"""
    corrected = []
    stats = {
        'total': len(ocr_results),
        'valid_room': 0,
        'invalid_room': 0,
        'corrected_room': 0,
        'errors': 0
    }
    
    for record in ocr_results:
        if 'error' in record:
            stats['errors'] += 1
            corrected.append({
                **record,
                'validation_status': 'error'
            })
            continue
        
        # Validate room number
        ocr_room = record.get('room_number', '-')
        validated_room = validate_room_number(room_db, ocr_room)
        
        if validated_room:
            if validated_room != ocr_room:
                stats['corrected_room'] += 1
                record['room_number'] = validated_room
                record['room_corrected'] = True
            else:
                stats['valid_room'] += 1
                record['room_corrected'] = False
        else:
            stats['invalid_room'] += 1
            record['room_corrected'] = False
        
        # Add room info from database
        if validated_room:
            room_info = next((r for r in room_db if r['room_number'] == validated_room), None)
            if room_info:
                record['building'] = room_info.get('building', '-')
                record['room_type'] = room_info.get('type', '-')
                record['price_per_night'] = room_info.get('price', 0)
        
        record['validation_status'] = 'validated'
        corrected.append(record)
    
    return corrected, stats

def print_summary(stats, corrected_results):
    """Print validation summary"""
    print("\n" + "=" * 80)
    print("📊 สรุปผลการตรวจสอบ (Validation Summary)")
    print("=" * 80)
    print(f"  ทั้งหมด: {stats['total']} รายการ")
    print(f"  ✅ ห้องถูกต้อง: {stats['valid_room']}")
    print(f"  🔧 แก้ไขแล้ว: {stats['corrected_room']}")
    print(f"  ❌ ห้องไม่ถูกต้อง: {stats['invalid_room']}")
    print(f"  ⚠️  Error: {stats['errors']}")
    print("=" * 80)
    
    # Show validated records
    print("\n📋 รายการที่ตรวจสอบแล้ว:")
    print(f"{'ไฟล์':<15} {'ห้อง (OCR)':<12} {'ห้อง (แก้)':<12} {'ชื่อ':<25} {'โทร':<15}")
    print("-" * 80)
    
    for r in corrected_results[:20]:  # Show first 20
        if r.get('validation_status') == 'validated':
            room_orig = r.get('room_number', '-')
            room_corrected = "✓" if r.get('room_corrected') else " "
            print(f"{r.get('source_file', ''):<15} {room_orig:<12} {room_corrected:<12} "
                  f"{r.get('guest_name', '-'):<25} {r.get('phone', '-'):<15}")
    
    print("=" * 80)

def main():
    print("🔍 Loading room database...")
    room_db = load_room_database()
    print(f"   Loaded {len(room_db)} rooms")
    
    print("🔍 Loading OCR results...")
    ocr_results = load_ocr_results()
    print(f"   Loaded {len(ocr_results)} records")
    
    print("🔍 Validating and correcting...")
    corrected, stats = validate_and_correct(ocr_results, room_db)
    
    # Save corrected results
    output_path = Path('results/ocr_result_validated.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(corrected, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved validated results → {output_path}")
    
    # Print summary
    print_summary(stats, corrected)

if __name__ == "__main__":
    main()
