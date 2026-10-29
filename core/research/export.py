"""Explicit user-download bundle; no automatic filesystem write or publishing."""
import hashlib
from html import escape
from io import BytesIO
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from .runs import export_bytes, validate, canonical


def bundle_bytes(run):
    validate(run)
    raw=export_bytes(run)
    evidence=escape(json.dumps(run,ensure_ascii=False,indent=2))
    report=('''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none';style-src 'unsafe-inline'">
<title>QUANTGEN ResearchRun</title><style>body{font:16px system-ui;max-width:960px;margin:40px auto;padding:20px;background:#f7f5f0;color:#193c31}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;border-radius:12px}</style>
<h1>QUANTGEN — ResearchRun</h1><p>Personal research. Execution completion is separate from investment validation.
P5–P95 is the central 90% simulated range, not a guarantee or confidence interval.
Reproducibility is PARTIAL: unknown vintage, rights and code state remain explicit.</p><pre>'''+evidence+'</pre>').encode()
    files={'research-run.json':raw,'report.html':report}
    files['MANIFEST.json']=(canonical({'format':'quantgen.research-bundle/1','files':
        {name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()}})+'\n').encode()
    buffer=BytesIO()
    with ZipFile(buffer,'w',compression=ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):
            info=ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED
            archive.writestr(info,data)
    return buffer.getvalue()
