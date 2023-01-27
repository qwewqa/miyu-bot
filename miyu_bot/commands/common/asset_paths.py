import hashlib
from pathlib import Path

_cache = {}


def clear_asset_filename_cache():
    _cache.clear()


def get_asset_filename(path):
    path = Path(path).resolve()
    if path in _cache:
        return _cache[path]
    if not path.exists():
        _cache[path] = "unknown.png"
        return "unknown.png"
    with path.open("rb") as f:
        result = f'{path.parent.relative_to(Path("assets").resolve()).as_posix()}/{path.stem}.{hashlib.sha256(f.read()).hexdigest()[:8]}{path.suffix}'
        result = result.split("/", 1)[1]
        _cache[path] = result
        return result
