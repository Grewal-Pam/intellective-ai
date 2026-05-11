"""
Simple migration helper: copies files from the existing `llm-prompt-repository` prompts into this repo's `prompts/` folder.
Run from workspace root:

    python intellective-ai/migrate_prompts.py

This script is intentionally conservative and will only copy `.md` and `.json` files.
"""
import os
import shutil

SRC = os.path.join(os.getcwd(), 'llm-prompt-repository')
DST = os.path.join(os.getcwd(), 'intellective-ai', 'prompts')

def migrate():
    if not os.path.exists(SRC):
        print('Source repo `llm-prompt-repository` not found in workspace root.')
        return
    os.makedirs(DST, exist_ok=True)
    count = 0
    for root, _, files in os.walk(SRC):
        for f in files:
            if f.lower().endswith(('.md', '.json')):
                src_path = os.path.join(root, f)
                rel = os.path.relpath(root, SRC)
                dst_dir = os.path.join(DST, rel)
                os.makedirs(dst_dir, exist_ok=True)
                dst_path = os.path.join(dst_dir, f)
                shutil.copy2(src_path, dst_path)
                count += 1
    print(f'Migrated {count} files to {DST}')

if __name__ == '__main__':
    migrate()
