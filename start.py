#!/usr/bin/env python3.12
"""Start Env Finder in Docker (-d by default) or a local Python 3.12 venv."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from settings import default_search_folder

PROJECT = Path(__file__).resolve().parent


def run(command: list[str], **kwargs):
    return subprocess.run(command, check=True, cwd=PROJECT, **kwargs)


def free_port(preferred: int) -> int:
    for port in (preferred, 0):
        with socket.socket() as listener:
            try:
                listener.bind(('127.0.0.1', port))
                return listener.getsockname()[1]
            except OSError:
                pass
    raise RuntimeError('Kein freier Port verfügbar.')


def start_docker(root: Path, directory: Path, preferred: int) -> None:
    if not shutil.which('docker'):
        raise RuntimeError('Docker fehlt. Installiere Docker Desktop oder verwende --local.')
    info = subprocess.run(['docker', 'info'], capture_output=True, text=True)
    if info.returncode:
        raise RuntimeError('Docker ist nicht erreichbar. Starte Docker Desktop und versuche es erneut.\n' + info.stderr.strip())
    image = 'env-finder:local'
    run(['docker', 'build', '-t', image, '.'])
    name = 'env-finder-' + str(time.time_ns())
    for attempt in range(5):
        port = free_port(preferred if attempt == 0 else 0)
        container = subprocess.run([
            'docker', 'run', '-d', '--name', name, '--restart', 'unless-stopped',
            '--publish', f'127.0.0.1:{port}:5000',
            '--mount', f'type=bind,source={root},target=/scan,readonly',
            '--env', f'ENV_FINDER_HOST_ROOT={root}',
            '--env', f'ENV_FINDER_DEFAULT={Path("/scan") / directory.relative_to(root)}',
            image,
        ], capture_output=True, text=True)
        if container.returncode == 0:
            break
        # Docker validates the mapping again; retry if another process took the port.
        subprocess.run(['docker', 'rm', name], capture_output=True)
        if 'port is already allocated' not in container.stderr and 'address already in use' not in container.stderr:
            raise RuntimeError(container.stderr.strip())
    else:
        raise RuntimeError('Docker konnte keinen freien Host-Port belegen.')
    url = f'http://127.0.0.1:{port}'
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url + '/health', timeout=2) as response:
                if json.load(response).get('status') == 'ok':
                    print(f'Env Finder läuft: {url}\nContainer: {name}\nSuchbereich: {root}\nStoppen: docker stop {name}', flush=True)
                    return
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            time.sleep(0.5)
    subprocess.run(['docker', 'logs', '--tail', '30', name])
    raise RuntimeError(f'Container {name} wurde gestartet, antwortet aber noch nicht. Prüfe docker logs {name}.')


def start_local(root: Path, directory: Path, port: int) -> None:
    python = shutil.which('python3.12')
    if not python:
        raise RuntimeError('Python 3.12 fehlt. Bitte python3.12 installieren.')
    venv = PROJECT / '.venv'
    interpreter = venv / 'bin' / 'python'
    if not interpreter.exists():
        run([python, '-m', 'venv', str(venv)])
    version = subprocess.check_output([str(interpreter), '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'], text=True).strip()
    if version != '3.12':
        raise RuntimeError('Die bestehende .venv verwendet nicht Python 3.12. Benenne sie um und starte erneut.')
    run([str(interpreter), '-m', 'pip', 'install', '-r', 'requirements.txt'])
    env = os.environ.copy()
    env.update(ENV_FINDER_ROOT=str(root), ENV_FINDER_DEFAULT=str(directory), ENV_FINDER_HOST_ROOT=str(root))
    run([str(interpreter), 'app.py', '--port', str(port)], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--local', action='store_true', help='Lokal mit .venv starten (Vordergrund).')
    mode.add_argument('--docker', action='store_true', help='Docker verwenden (Standard).')
    parser.add_argument('-d', '--detach', action='store_true', help='Docker läuft immer im Hintergrund.')
    parser.add_argument('--root', type=Path, help='Freigegebener Suchbereich; Standard: DEFAULT_SEARCH_FOLDER aus .env.')
    parser.add_argument('--directory', type=Path, help='Anfangs ausgewählter Ordner; Standard: Suchbereich.')
    parser.add_argument('--port', type=int, default=5000, help='Bevorzugter Port; bei Belegung automatisch ausweichen.')
    args = parser.parse_args()
    try:
        root = (args.root or default_search_folder()).expanduser().resolve()
        directory = (args.directory or root).expanduser().resolve()
        if not 1 <= args.port <= 65535:
            raise RuntimeError('Der Port muss zwischen 1 und 65535 liegen.')
        if not root.is_dir() or not directory.is_dir():
            raise RuntimeError('Suchbereich und Startverzeichnis müssen existierende Verzeichnisse sein.')
        if not directory.is_relative_to(root):
            raise RuntimeError('Das Startverzeichnis muss im Suchbereich liegen.')
        if ',' in str(root) and not args.local:
            raise RuntimeError('Docker-Suchbereiche mit Kommas im Pfad werden nicht unterstützt. Verwende --local.')
        if args.local:
            if args.detach:
                raise RuntimeError('-d ist nur für Docker vorgesehen. Verwende --docker -d.')
            start_local(root, directory, args.port)
        else:
            start_docker(root, directory, args.port)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Fehler: {error}\n')
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
