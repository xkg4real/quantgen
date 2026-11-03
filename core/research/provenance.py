"""Bounded provenance: only named calculation modules, never store traversal."""
import hashlib
import importlib.metadata
from pathlib import Path
import platform
import subprocess

from core.app_paths import application_root


def code_evidence():
    root=application_root(); commit=None
    if (root / '.git').exists():
        try:
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,timeout=2,stderr=subprocess.DEVNULL).decode().strip()
        except (OSError,subprocess.SubprocessError): pass
    # Deliberately fixed list. No .env, stores, research cards or git diff scan.
    base=Path(__file__).resolve().parents[1] / 'quant'
    digest=hashlib.sha256()
    for name in ('montecarlo.py','garch.py','history.py'):
        p=base/name
        if not p.is_file(): return dict(commit=commit,working_tree='NOT_VERIFIED',calculation_sha256=None)
        digest.update(name.encode()+b'\0'+p.read_bytes()+b'\0')
    return dict(commit=commit,working_tree='NOT_VERIFIED',calculation_sha256=digest.hexdigest())


def runtime_evidence():
    result={'python':platform.python_version()}
    for name in ('numpy','scipy','pandas','quantgen'):
        try: result[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: result[name]='NOT_RECORDED'
    return result
