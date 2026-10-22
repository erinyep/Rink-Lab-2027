"""Content-addressed snapshots: corrections create versions, never replace records."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def archive_snapshot(source, root, kind):
    source, root = Path(source), Path(root)
    manifest = json.loads((source / 'manifest.json').read_text())
    files = dict(manifest['files'])
    files['manifest.json'] = digest(source / 'manifest.json')
    for name, expected in files.items():
        if digest(source / name) != expected:
            raise ValueError('Changed source: ' + str(source / name))
    destination = root / kind / files['manifest.json']
    if destination.exists():
        for name, expected in files.items():
            if digest(destination / name) != expected:
                raise ValueError('Changed archive: ' + str(destination / name))
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A complete staged directory is renamed into place so interrupted copies
    # cannot be mistaken for accepted historical records.
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        stage = Path(temp) / 'snapshot'
        stage.mkdir()
        for name in files:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        stage.rename(destination)
    return destination
