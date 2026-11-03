"""Explicit native analysis reports, separate from official ResearchRun gates."""
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import hashlib
import json
import math
from zipfile import ZipFile, ZIP_DEFLATED

from .presentation import safe_detail


def plain(value):
    if is_dataclass(value): return plain(asdict(value))
    if isinstance(value, dict): return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [plain(v) for v in value]
    if hasattr(value, 'tolist'): return plain(value.tolist())
    if isinstance(value, float): return value if math.isfinite(value) else None
    if isinstance(value, str): return safe_detail(value, limit=None)
    if value is None or isinstance(value, (bool,int)): return value
    raise TypeError('Unsupported report value')


def make_report(tool, request, sections):
    from .provenance import code_evidence, runtime_evidence
    return dict(format='quantgen.analysis-report/1', tool=tool, created_at=datetime.now(timezone.utc).isoformat(),
                execution_status='COMPLETED', verdict='NOT_RUN', reproducibility='PARTIAL',
                data_rights='NOT_VERIFIED', parameters=plain(request), sections=plain(sections),
                code=code_evidence(), environment=runtime_evidence())


def report_bytes(report, *, bundle=False, locale=None):
    if report.get('format') != 'quantgen.analysis-report/1' or report.get('verdict') != 'NOT_RUN':
        raise ValueError('Unsupported report contract')
    raw = (json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if not bundle: return raw
    html = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\'">'
            '<title>QUANTGEN analysis report</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:24px;background:#f7f5f0;color:#194c40}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
            '<h1>QUANTGEN — '+escape(report['tool'])+'</h1><p>Personal research. Calculation completed; official validation NOT_RUN. '
            'Reproducibility PARTIAL. Non-finite observations are null. This report does not approve a model or a trade.</p><pre>'
            +escape(raw.decode())+'</pre>').encode()
    if locale is not None:
        from core.i18n import LocaleContext
        from .localized_report import localized_html
        ctx=locale if isinstance(locale,LocaleContext) else LocaleContext(locale)
        html=localized_html(report,ctx,title='QUANTGEN · '+ctx.text(report['tool']))
    files={'analysis.json':raw,'report.html':html}
    files['MANIFEST.json']=json.dumps({'files':{n:{'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()} for n,d in files.items()}},indent=2).encode()
    out=BytesIO()
    with ZipFile(out,'w',ZIP_DEFLATED) as z:
        for name,data in files.items(): z.writestr(name,data)
    return out.getvalue()
