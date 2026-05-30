import random
import string
import json
from pathlib import Path
from datetime import datetime

def generate_license_key():
    """Generate a valid license key in the format WWIP-XXXX-YYYY-ZZZZ"""
    def generate_block():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    year = datetime.now().year  # e.g., 2025
    return f"WWIP-{generate_block()}-{year}-{generate_block()}"

def save_valid_keys(num_keys=10):
    """Generate and save valid license keys"""
    keys = [generate_license_key() for _ in range(num_keys)]
    
    # Save keys to a file
    keys_file = Path(__file__).parent / 'valid_license_keys.json'
    with open(keys_file, 'w') as f:
        json.dump({'valid_keys': keys}, f, indent=4)
    
    return keys

if __name__ == '__main__':
    # Generate 10 valid license keys
    keys = save_valid_keys(10)
    print("Generated license keys:")
    for key in keys:
        print(key)