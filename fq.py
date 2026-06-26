"""
Removes GUI checkbox-iteration blocks from osdag_core call_3D* functions.
Handles all known patterns.
"""

import re
import sys
from pathlib import Path

PATTERNS = [
    # Pattern 1: simple setChecked(False) via .children()
    re.compile(
        r'( +)for chkbox in ui\.\w+\.children\(\):\r?\n'
        r'(?:\1 +if chkbox\.objectName\(\)[^\n]+\r?\n\1 +continue\r?\n)?'
        r'(?:\1 +if isinstance\(chkbox, QCheckBox\):\r?\n\1 +chkbox\.setChecked\(False\)\r?\n)+'
    ),
    # Pattern 2: blockSignals variant via .children()
    re.compile(
        r'( +)for chkbox in ui\.\w+\.children\(\):\r?\n'
        r'(?:\1 +if chkbox\.objectName\(\)[^\n]+\r?\n\1 +continue\r?\n)?'
        r'(?:\1 +if isinstance\(chkbox, QCheckBox\):\r?\n'
        r'(?:\1 +#[^\n]+\r?\n)?'
        r'\1 +chkbox\.blockSignals\(True\)\r?\n'
        r'\1 +chkbox\.setChecked\(False\)\r?\n'
        r'\1 +chkbox\.blockSignals\(False\)\r?\n)+'
    ),
    # Pattern 3: findChildren(QtWidgets.QCheckBox) with setChecked(False)
    re.compile(
        r'( +)for chkbox in ui\.findChildren\(QtWidgets\.QCheckBox\):\r?\n'
        r'(?:\1 +if chkbox\.objectName\(\)[^\n]+\r?\n\1 +continue\r?\n)?'
        r'(?:\1 +if isinstance\(chkbox, QCheckBox\):\r?\n\1 +chkbox\.setChecked\(False\)\r?\n)+'
    ),
    # Pattern 4: frame.children() with setChecked(Qt.Unchecked) — may have getattr guard
    re.compile(
        r'( +)(?:frame = getattr\(ui, ["\']frame["\'], None\)\r?\n'
        r'\1 +if frame:\r?\n'
        r'\1 +    for chkbox in frame\.children\(\):\r?\n'
        r'(?:\1 +    +if chkbox\.objectName\(\)[^\n]+\r?\n\1 +    +continue\r?\n)?'
        r'\1 +    +if isinstance\(chkbox, QCheckBox\):\r?\n'
        r'\1 +    +chkbox\.setChecked\(Qt\.Unchecked\)\r?\n)'
    ),
    # Pattern 5: ui.frame.children() directly with setChecked(Qt.Unchecked)
    re.compile(
        r'( +)for chkbox in ui\.frame\.children\(\):\r?\n'
        r'(?:\1 +if chkbox\.objectName\(\)[^\n]+\r?\n\1 +continue\r?\n)?'
        r'(?:\1 +if isinstance\(chkbox, QCheckBox\):\r?\n\1 +chkbox\.setChecked\(Qt\.Unchecked\)\r?\n)+'
    ),
]

def fix_file(path: Path) -> int:
    try:
        original = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return 0
    text = original
    total = 0
    for pat in PATTERNS:
        text, count = pat.subn('', text)
        total += count
    if total:
        path.write_text(text, encoding='utf-8')
        print(f"  [{total} block(s) removed] {path.name}")
    return total

def main(root: Path):
    files_changed = 0
    for py_file in root.rglob('*.py'):
        if fix_file(py_file):
            files_changed += 1
    print(f"\nDone. {files_changed} file(s) modified.")

if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    main(root)