"""Produce a guarded, minimal UI-only patch against the captured live source."""
import hashlib
import json
import re
from pathlib import Path

import argparse
parser=argparse.ArgumentParser(description='Rebuild the already-deployed UI artifact; does not deploy.')
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
source=args.source.read_text()
assert hashlib.sha256(source.encode()).hexdigest()=='eb392040377722562ee5d5ca175629c2156186c5bd55a3aec9792dce8b2a643f'
patches=[]
def replace(old,new):
    global source
    assert source.count(old)==1,('Unexpected source match count',old[:90],source.count(old))
    patches.append({'old':old,'new':new})
    source=source.replace(old,new)

replace("  const navInd = document.createElement('span');", "  // Discard decoration retained in a saved/rendered copy of this page.\n  $$('.nav-links > .nav-ind').forEach(el => el.remove());\n  const navInd = document.createElement('span');")
replace("  function glide(box, activeSel, labelSel) {\n    const thumb", "  function glide(box, activeSel, labelSel) {\n    // Rebuild generated decoration once; retain the actual labels and inputs.\n    box.querySelectorAll(':scope > span[aria-hidden=\"true\"]').forEach(el => el.remove());\n    const thumb")
replace("    const dpr = Math.min(2, window.devicePixelRatio || 1);", "    const dpr = Math.max(1, window.devicePixelRatio || 1);")
replace("    const L = narrow ? 40 : 52, T = 34, B = 30, histW = Math.round(w * (narrow ? 0.2 : 0.18));\n    const R = w - histW - 18;\n    const H = r.horizon;\n    const [lo, hi] = r._range || labRange(r);",
"""    const T = 34, B = 30, histW = Math.round(w * (narrow ? 0.2 : 0.18));
    const R = w - histW - 18;
    const H = r.horizon;
    const [lo, hi] = r._range || labRange(r);
    const ticks = niceTicks(lo, hi, 5);
    c.font = '400 11px "IBM Plex Mono", ui-monospace, monospace';
    const axisWidth = Math.max(0, ...ticks.map(v => c.measureText(v.toFixed(0)).width));
    const L = Math.max(narrow ? 40 : 52, Math.ceil(axisWidth) + 12);""")
replace("    niceTicks(lo, hi, 5).forEach(v => { const y", "    ticks.forEach(v => { const y")
replace("    const tag = (s, x, y, col) => { c.lineWidth = 4; c.strokeStyle = P.bg; c.strokeText(s, x, y); c.fillStyle = col; c.fillText(s, x, y); };",
"""    const labels = [];
    const tag = (s, x, y, col) => {
      const metrics = c.measureText(s), width = Math.min(metrics.width, w - 8);
      const left = Math.max(4, Math.min(w - 4 - width, c.textAlign === 'right' ? x - width : x));
      const height = metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent;
      const base = Math.max(T + height, Math.min(h - B - 4, y));
      const fits = bottom => labels.every(b => left + width + 4 <= b.left || left >= b.right + 4 ||
        bottom + 3 <= b.top || bottom - height >= b.bottom + 3);
      y = base;
      for (let step = 0; step < 8; step++) {
        const candidates = step ? [base - step * 16, base + step * 16] : [base];
        const position = candidates.find(bottom => bottom >= T + height && bottom <= h - B - 4 && fits(bottom));
        if (position !== undefined) { y = position; break; }
      }
      labels.push({left, right: left + width, top: y - height, bottom: y});
      c.save(); c.textAlign = 'left'; c.lineWidth = 4; c.strokeStyle = P.bg;
      c.strokeText(s, left, y, w - 8); c.fillStyle = col; c.fillText(s, left, y, w - 8); c.restore();
    };""")
replace("    const wrap = $('#units'), read = $('#unitRead'), mini = $('#miniUnits');", "    const wrap = $('#units'), read = $('#unitRead'), mini = $('#miniUnits');\n    // Saved cards are a no-JavaScript fallback; replace them with interactive cards.\n    wrap.replaceChildren(); mini.replaceChildren();")
replace("  function buildGrades() {\n    const box = $('#grades');", "  function buildGrades() {\n    const box = $('#grades');\n    box.querySelectorAll(':scope > .g-row').forEach(row => row.remove());")
replace("  .record { gap: 24px; }", "  /* A twelve-column grid still reserves eleven gaps when every child spans it. */\n  .record, .rule-row, .sources, .repro, .contrib, .foot-grid, .gate-scene, .coda { grid-template-columns: minmax(0, 1fr); }\n  .record > *, .rule-row > *, .sources > *, .repro > *, .contrib > *, .foot-grid > *, .gate-scene > *, .coda > * { min-width: 0; }\n  .record { gap: 24px; }")
stale=re.findall(r'<script\b[^>]*src="QUANTGEN_files/[^\"]+"[^>]*></script>',source)
assert len(stale)==1
replace(stale[0],'<!-- Removed missing saved-page analytics asset; application scripts are inline. -->')
replace('</head>', '<meta name="qg-ui-revision" content="2026-10-31.1">\n</head>')

expected='d3dcc4f48dd2355fc7e748f30b75135992043a0e9933dc13f40d7355d624ca02'
assert hashlib.sha256(source.encode()).hexdigest()==expected, 'Unexpected reconstructed artifact'
assert args.source.resolve()!=args.output.resolve(), 'Never overwrite source'
with args.output.open('x') as target:
    target.write(source)
print(json.dumps({'sha256':expected,'bytes':len(source.encode()),'output':str(args.output)}))
