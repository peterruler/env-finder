"""Find .env files and display their contents locally (Python 3.12)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import socket
import stat
import time

from flask import Flask, jsonify, render_template, request
from waitress import serve
from settings import default_search_folder

MAX_RESULTS = 10_000
MAX_SCAN_SECONDS = 120
MAX_CONTENT_BYTES = 1024 * 1024


def create_app(root: Path | None = None, default: Path | None = None) -> Flask:
    app = Flask(__name__)
    root = Path(root or os.environ.get('ENV_FINDER_ROOT') or default_search_folder()).expanduser().resolve()
    default = Path(default or os.environ.get('ENV_FINDER_DEFAULT', root)).expanduser().resolve()
    display_root = os.environ.get('ENV_FINDER_HOST_ROOT', str(root))
    app.config.update(MAX_CONTENT_LENGTH=4096, TRUSTED_HOSTS=['localhost', '127.0.0.1', '[::1]'])

    def checked_path(value: str, *, directory: bool = True) -> Path:
        path = Path(value).expanduser()
        if str(root) != display_root and path.is_absolute():
            try:
                path = root / path.relative_to(Path(display_root))
            except ValueError:
                pass
        if not path.is_absolute():
            path = root / path
        if not directory and any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError('Symbolische Links werden nicht geöffnet.')
        try:
            path = path.resolve(strict=True)
            path.relative_to(root)
        except FileNotFoundError:
            raise ValueError('Die Datei oder das Verzeichnis existiert nicht.') from None
        except (ValueError, OSError, RuntimeError):
            raise ValueError('Das Verzeichnis liegt außerhalb des freigegebenen Suchbereichs.') from None
        if directory and not path.is_dir():
            raise ValueError('Bitte ein Verzeichnis auswählen.')
        if not directory and (not path.is_file() or not (path.name == '.env' or path.name.startswith('.env.'))):
            raise ValueError('Es können nur .env- und .env.*-Dateien geöffnet werden.')
        return path

    def shown_path(path: Path) -> str:
        return str(Path(display_root) / path.relative_to(root))

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        return response

    @app.errorhandler(ValueError)
    def invalid_path(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(PermissionError)
    def denied(error):
        return jsonify(error='Keine Leseberechtigung für diese Datei oder dieses Verzeichnis.'), 403

    @app.errorhandler(OSError)
    def filesystem_error(error):
        return jsonify(error='Die Datei oder das Verzeichnis kann momentan nicht gelesen werden.'), 400

    @app.get('/')
    def index():
        return render_template('index.html', default=shown_path(default), display_default=shown_path(default), display_root=display_root)

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    @app.get('/api/content')
    def content():
        path = checked_path(request.args.get('path', ''), directory=False)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError('Es können nur reguläre Dateien geöffnet werden.')
            raw = source.read(MAX_CONTENT_BYTES + 1)
        truncated = len(raw) > MAX_CONTENT_BYTES
        raw = raw[:MAX_CONTENT_BYTES]
        warnings = []
        if truncated:
            warnings.append('Die Inhaltsanzeige ist auf 1 MiB pro Datei begrenzt.')
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = raw.decode('utf-8-sig', errors='replace')
            warnings.append('Ungültige UTF-8-Zeichen wurden durch Ersatzzeichen dargestellt.')
        return jsonify(path=shown_path(path), content=text, truncated=truncated, warnings=warnings)

    @app.get('/api/directories')
    def directories():
        path = checked_path(request.args.get('path', str(default)))
        children = []
        skipped = 0
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        children.append({'name': entry.name, 'path': shown_path(Path(entry.path))})
                except OSError:
                    skipped += 1
        children.sort(key=lambda item: item['name'].casefold())
        return jsonify(path=shown_path(path), display_path=shown_path(path), parent=shown_path(path.parent) if path != root else None, directories=children, skipped=skipped)

    @app.get('/api/search')
    def search():
        path = checked_path(request.args.get('path', str(default)))
        variants = request.args.get('variants', 'false') == 'true'
        bounded = request.args.get('bounded', 'false') == 'true'
        started = time.monotonic()
        files = []
        warnings = []
        skipped = 0
        visited = 0
        pending = [path]
        truncated = False
        while pending:
            if bounded and time.monotonic() - started >= MAX_SCAN_SECONDS:
                truncated = True
                warnings.append(f'Die Suche wurde nach {MAX_SCAN_SECONDS} Sekunden begrenzt. Wähle einen kleineren Ordner.')
                break
            current = pending.pop()
            try:
                with os.scandir(current) as entries:
                    visited += 1
                    for entry in entries:
                        if bounded and time.monotonic() - started >= MAX_SCAN_SECONDS:
                            truncated = True
                            warnings.append(f'Die Suche wurde nach {MAX_SCAN_SECONDS} Sekunden begrenzt. Wähle einen kleineren Ordner.')
                            break
                        try:
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                pending.append(Path(entry.path))
                            elif (entry.name == '.env' or (variants and entry.name.startswith('.env.'))) and entry.is_file(follow_symlinks=False):
                                metadata = entry.stat(follow_symlinks=False)
                                found = Path(entry.path)
                                files.append({'name': entry.name, 'path': shown_path(found), 'relative_path': str(found.relative_to(path)), 'size': metadata.st_size, 'modified': datetime.fromtimestamp(metadata.st_mtime, timezone.utc).isoformat()})
                                if len(files) >= MAX_RESULTS:
                                    truncated = True
                                    warnings.append(f'Die Suche wurde auf {MAX_RESULTS} Treffer begrenzt.')
                                    break
                        except OSError:
                            skipped += 1
            except OSError:
                skipped += 1
            if truncated:
                break
        if skipped:
            warnings.append(f'{skipped} Dateien oder Verzeichnisse konnten nicht gelesen werden.')
        files.sort(key=lambda item: item['relative_path'].casefold())
        return jsonify(files=files, count=len(files), directory=shown_path(path), visited=visited, skipped=skipped, truncated=truncated, warnings=warnings, elapsed=round(time.monotonic() - started, 3))

    return app


def bind_available(host: str, preferred: int) -> socket.socket:
    """Reserve the listener so another process cannot claim it during startup."""
    for port in (preferred, 0):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind((host, port))
            listener.listen(128)
            return listener
        except OSError:
            listener.close()
    raise RuntimeError('Es konnte kein freier Port geöffnet werden.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    listener = bind_available(args.host, args.port)
    port = listener.getsockname()[1]
    print(f'Env Finder: http://127.0.0.1:{port}', flush=True)
    serve(create_app(), sockets=[listener], threads=4)
