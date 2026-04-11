#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch translate all strings using deep-translator (efficient)
Usage: python scripts/translate_batch.py
"""

import sys
from pathlib import Path
import time

try:
    from deep_translator import GoogleTranslator
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "deep-translator", "-q"])
    from deep_translator import GoogleTranslator

try:
    import polib
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "polib", "-q"])
    import polib

LOCALES_DIR = Path("locales")
DOMAIN = "ddt4all"

LANGUAGE_MAP = {
    'es': 'es', 'fr': 'fr', 'pt': 'pt', 'de': 'de', 'it': 'it',
    'cs_CZ': 'cs', 'nl': 'nl', 'hu': 'hu', 'pl': 'pl', 'ro': 'ro',
    'ru': 'ru', 'sr': 'sr', 'tr': 'tr', 'uk_UA': 'uk',
}

def translate_po_file(lang_code, lang_dest):
    """Translate all empty strings at once"""
    po_path = LOCALES_DIR / lang_code / "LC_MESSAGES" / f"{DOMAIN}.po"
    if not po_path.exists():
        return 0
    
    po = polib.pofile(str(po_path))
    translator = GoogleTranslator(source='en', target=lang_dest)
    
    # Translate ALL strings (even those that already have translation)
    # all_entries = [e for e in po if e.msgid and e.msgid.strip()]
    all_entries = [e for e in po if e.msgid]
    if not all_entries:
        print(f"  [{lang_code}] Nothing to translate")
        return 0
    
    total = len(all_entries)
    print(f"  [{lang_code}] {total} strings to translate (ALL)")
    
    translated = 0
    batch_size = 50
    
    for i in range(0, total, batch_size):
        batch = all_entries[i:i+batch_size]
        texts = [e.msgid for e in batch]
        
        try:
            # Translate batch
            results = translator.translate_batch(texts)
            
            for entry, result in zip(batch, results):
                if result:
                    entry.msgstr = None
                    entry.msgstr = result
                    translated += 1
            
            print(f"  [{lang_code}] {min(i+batch_size, total)}/{total}")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  [ERROR {lang_code}] {e}")
            time.sleep(2)
    
    po.save()
    print(f"  [{lang_code}] {translated}/{total} translated")
    return translated

def main():
    print("Batch translating (faster)...\n")
    total = 0
    
    for lang_code, lang_dest in LANGUAGE_MAP.items():
        print(f"\n=== {lang_code.upper()} ===")
        count = translate_po_file(lang_code, lang_dest)
        total += count
        if count > 0:
            time.sleep(1)
    
    print(f"\n[SUMMARY] Total: {total} strings translated")
    print("\nCompiling .mo files...")
    import subprocess
    subprocess.run([sys.executable, "scripts/i18n.py", "po-to-mo"])

if __name__ == "__main__":
    main()
