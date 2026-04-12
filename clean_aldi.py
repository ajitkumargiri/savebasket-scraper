import json
import os
import re
from pathlib import Path

def clean_product_name(text):
    """Clean and normalize product name."""
    if not text:
        return text
    
    text = text.lower()
    
    unit_mappings = {
        r'\blitre\b': 'l',
        r'\bliter\b': 'l',
        r'\bgramme\b': 'g',
        r'\bgram\b': 'g',
        r'\bkilogram\b': 'kg',
        r'\bkg\b': 'kg',
        r'\bmillilitre\b': 'ml',
        r'\bmilliliter\b': 'ml',
        r'\bml\b': 'ml',
    }
    
    for old, new in unit_mappings.items():
        text = re.sub(old, new, text, flags=re.IGNORECASE)
    
    text = re.sub(r'[^\w\s\-/]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_price(text):
    """Clean and normalize price strings."""
    if not text:
        return None
    
    text = re.sub(r'[^\d,.]', '', text).strip()
    
    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        text = text.replace(',', '.')
    
    try:
        return float(text)
    except ValueError:
        return None


def find_latest_aldi_file():
    """Find the latest ALDI JSON file in output directory."""
    output_dir = Path('output')
    if not output_dir.exists():
        print(f"Error: output/ directory not found")
        return None
    
    aldi_files = list(output_dir.glob('aldi_*.json'))
    aldi_files = [f for f in aldi_files if 'cleaned' not in f.name]
    
    if not aldi_files:
        print("Error: No aldi_*.json files found in output/")
        return None
    
    latest = max(aldi_files, key=lambda p: p.stat().st_mtime)
    return latest


def clean_aldi_json(input_path=None, output_path='output/aldi_cleaned.json'):
    """Clean ALDI JSON data."""
    if input_path is None:
        input_path = find_latest_aldi_file()
        if input_path is None:
            return None
    
    print(f"Reading from: {input_path}")
    print(f"Writing to: {output_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    print(f"Found {len(products)} products")
    
    cleaned = []
    for p in products:
        cleaned_product = {
            'store': p.get('store', 'ALDI'),
            'brand': p.get('brand', ''),
            'name': clean_product_name(p.get('name', '')),
            'price': clean_price(p.get('price', '')),
            'quantity': clean_product_name(p.get('size', '')),
            'link': p.get('link', ''),
            'image': p.get('image', ''),
        }
        cleaned.append(cleaned_product)
    
    try:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        print(f"Success! Cleaned {len(cleaned)} products and saved to {output_path}")
        return cleaned
    except Exception as e:
        print(f"Error writing file: {e}")
        return None


if __name__ == "__main__":
    clean_aldi_json()
