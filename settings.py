"""Read the shared search-folder setting without requiring an installed venv."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shlex

PROJECT = Path(__file__).resolve().parent


def default_search_folder(env_file: Path | None = None) -> Path:
    env_file = env_file if env_file is not None else PROJECT / '.env'
    value = os.environ.get('DEFAULT_SEARCH_FOLDER')
    if value is None:
        try:
            lines = env_file.read_text(encoding='utf-8-sig').splitlines()
        except FileNotFoundError:
            lines = []
        for line in lines:
            match = re.match(r'^\s*(?:export\s+)?DEFAULT_SEARCH_FOLDER\s*=\s*(.*)$', line)
            if match:
                value = match.group(1).strip()
                if value.startswith(('"', "'")):
                    try:
                        parts = shlex.split(value, comments=True)
                    except ValueError:
                        raise RuntimeError('DEFAULT_SEARCH_FOLDER enthält ungültige Anführungszeichen.') from None
                    if len(parts) != 1:
                        raise RuntimeError('DEFAULT_SEARCH_FOLDER muss genau einen Verzeichnispfad enthalten.')
                    value = parts[0]
                else:
                    value = re.split(r'\s+#', value, maxsplit=1)[0].strip()
    if value is None or not value.strip():
        raise RuntimeError('DEFAULT_SEARCH_FOLDER fehlt oder ist leer. Setze den Wert in .env (Vorlage: .env.example) oder übergib --root.')
    folder = Path(value.strip()).expanduser()
    return folder if folder.is_absolute() else env_file.parent / folder
