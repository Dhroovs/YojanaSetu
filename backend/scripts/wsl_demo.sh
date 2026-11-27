#!/usr/bin/env bash
# Existing-runtime launcher. Run as the unprivileged Linux demo user.
set -euo pipefail
task_backend="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_runtime="$HOME/.local/share/yojanasetu-runtime"
task_node="$(find "$task_runtime" -maxdepth 1 -type d -name 'node-v24.*-linux-x64' | sort -V | tail -1)"
if [[ -z "$task_node" || ! -x "$task_runtime/venv/bin/python" ]]; then
    echo 'Install the isolated Python environment and Node 24 first; see docs/LOCAL_DEMO_ACCESS.md.' >&2
    exit 1
fi
export PATH="$task_node/bin:$task_runtime/venv/bin:$PATH"
export MONGODB_URI=mongodb://127.0.0.1:27018
export MONGODB_DATABASE=yojanasetu_linux_catalogue
export CHROMA_PATH="$task_runtime/catalogue/chroma"
export DOCUMENT_STORAGE_PATH="$task_runtime/catalogue/private-documents"
export ENABLE_AI=true LLM_PROVIDER=none ALLOW_HOSTED_LLM=false ANONYMIZED_TELEMETRY=false
export YOJANASETU_FRONTEND_DIRECTORY="$task_runtime/frontend"
export NODE_BINARY="$task_node/bin/node"
cd "$task_backend"
if [[ "${1:-status}" == start ]]; then
    python - "$task_backend" "$task_runtime" <<'PY'
import shutil, socket, subprocess, sys
from pathlib import Path
from pymongo import MongoClient
backend, runtime = map(Path, sys.argv[1:])
with socket.socket() as connection:
    running = connection.connect_ex(('127.0.0.1', 27018)) == 0
if not running:
    subprocess.run(['mongod', '--dbpath', str(runtime / 'mongo'), '--bind_ip',
                    '127.0.0.1', '--port', '27018', '--logpath', str(runtime / 'mongo.log'),
                    '--fork'], check=True)
with MongoClient('mongodb://127.0.0.1:27018', serverSelectionTimeoutMS=3000) as mongo:
    actual = Path(mongo.admin.command('getCmdLineOpts')['parsed']['storage']['dbPath'])
    if actual.resolve() != (runtime / 'mongo').resolve():
        raise RuntimeError('Port 27018 belongs to a different database; refusing to use it')
shutil.copytree(backend.parent / 'frontend', runtime / 'frontend', dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('node_modules', 'dist', '*.tsbuildinfo', '.env'))
PY
fi
exec python -m scripts.local_demo "${1:-status}"
