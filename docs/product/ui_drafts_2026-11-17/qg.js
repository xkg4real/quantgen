// QUANTGEN draft helpers: the rail and simple SVG charts drawn like the app's QPainter charts.
const NAV = [["home","연구 홈"],["markets","시장"],["tools","분석 도구"],["guide","기술지표 가이드"],["quant","설계/검증"],["risk","분석"],["library","연구 보관함"],["system","시스템"]];
function rail(active) {
  const el = document.createElement("aside"); el.className = "rail";
  el.innerHTML = `<div class="brand"><div class="mark"><svg width="20" height="20" viewBox="0 0 20 20"><path d="M15 5a7 7 0 1 0 0 10" fill="none" stroke="#194C40" stroke-width="2.2" stroke-linecap="round"/><path d="M8 10h8" stroke="#194C40" stroke-width="2.2" stroke-linecap="round"/></svg></div><div class="word">QUANTGEN</div><div class="toggle"></div></div>
  <nav class="nav">${NAV.map(([k,t]) => `<a class="${k===active?'on':''}">${t}</a>`).join("")}</nav>
  <div class="bottom"><div class="halt">모의 엔진 긴급 정지</div><div class="select">밝게</div><div class="cap">언어</div><div class="select">한국어</div></div>`;
  document.body.prepend(el);
}
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function walk(n, start, vol, seed, drift = 0) { const r = rng(seed); const out = [start]; for (let i = 1; i < n; i++) out.push(out[i-1] * (1 + drift + (r() - .5) * vol)); return out; }
const NS = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }
function scale(values, lo, hi, a, b) { return v => b - (v - lo) / (hi - lo || 1) * (b - a); }
function fmt(v, d = 0) { return v.toLocaleString("ko-KR", { minimumFractionDigits: d, maximumFractionDigits: d }); }
// A line chart with a right axis (as the stock detail draws its price axis). Values may be null (a gap).
// svg with data-fit: sized to its parent's box first.
function fit(svg) { if (svg.dataset.fit !== undefined) { const r = svg.parentElement.getBoundingClientRect(); const dh = +(svg.dataset.fit || 0);
  svg.setAttribute("width", Math.floor(r.width - (+svg.dataset.padx || 0))); svg.setAttribute("height", Math.floor(r.height - dh)); } }
function lineChart(svg, series, opt = {}) {
  fit(svg);
  const W = +svg.getAttribute("width"), H = +svg.getAttribute("height"); const padR = opt.padR ?? 64, padB = opt.padB ?? 22, padT = opt.padT ?? 8;
  const all = series.flatMap(s => s.values).concat((opt.bands || []).flatMap(b => b.upper.concat(b.lower))).filter(v => v !== null && v !== undefined);
  let lo = opt.lo ?? Math.min(...all), hi = opt.hi ?? Math.max(...all); const m = (hi - lo) * .06; if (opt.lo === undefined) lo -= m; if (opt.hi === undefined) hi += m;
  const y = scale(all, lo, hi, padT, H - padB); const n = Math.max(...series.map(s => s.values.length), ...(opt.bands || []).map(b => b.upper.length)); const x = i => i / (n - 1) * (W - padR);
  const ticks = opt.ticks ?? 4;
  for (let k = 0; k <= ticks; k++) { const v = lo + (hi - lo) * k / ticks, yy = y(v);
    svg.append(svgEl("line", { x1: 0, x2: W - padR, y1: yy, y2: yy, stroke: "#ECEDE5", "stroke-dasharray": "3 4" }));
    const t = svgEl("text", { x: W - padR + 10, y: yy + 4, "font-size": 11, fill: "#646E68" }); t.textContent = (opt.prefix || "") + fmt(v, opt.digits ?? 0) + (opt.suffix || ""); svg.append(t); }
  (opt.hlines || []).forEach(([v, col, dash]) => svg.append(svgEl("line", { x1: 0, x2: W - padR, y1: y(v), y2: y(v), stroke: col, "stroke-dasharray": dash || "4 4" })));
  (opt.zones || []).forEach(([a, b, fill]) => svg.append(svgEl("rect", { x: 0, y: y(b), width: W - padR, height: y(a) - y(b), fill })));
  (opt.bands || []).forEach(b => { const idx = b.upper.map((v, i) => i).filter(i => b.upper[i] !== null && b.upper[i] !== undefined);
    const pts = idx.map(i => `${x(i)},${y(b.upper[i])}`).concat(idx.slice().reverse().map(i => `${x(i)},${y(b.lower[i])}`)); svg.append(svgEl("polygon", { points: pts.join(" "), fill: b.fill, stroke: "none" })); });
  series.forEach(s => { let d = "", pen = false; s.values.forEach((v, i) => { if (v === null || v === undefined) { pen = false; return; } d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`; pen = true; });
    svg.append(svgEl("path", { d, fill: "none", stroke: s.color, "stroke-width": s.width || 1.8, "stroke-dasharray": s.dash || "" })); });
  (opt.vlines || []).forEach(([i, col]) => svg.append(svgEl("line", { x1: x(i), x2: x(i), y1: padT, y2: H - padB, stroke: col || "#9AA29C", "stroke-dasharray": "3 3" })));
  (opt.xlabels || []).forEach(([i, t]) => { const e = svgEl("text", { x: Math.min(Math.max(x(i), 14), W - padR - 14), y: H - 5, "font-size": 11, fill: "#646E68", "text-anchor": "middle" }); e.textContent = t; svg.append(e); });
  if (opt.last) { const s = series[opt.lastIndex || 0]; const vals = s.values.filter(v => v !== null); const v = vals[vals.length - 1]; const yy = y(v);
    svg.append(svgEl("line", { x1: 0, x2: W - padR, y1: yy, y2: yy, stroke: s.color, "stroke-dasharray": "2 3", opacity: .6 }));
    svg.append(svgEl("rect", { x: W - padR + 4, y: yy - 10, width: padR - 6, height: 20, rx: 4, fill: s.color }));
    const t = svgEl("text", { x: W - padR + 9, y: yy + 4, "font-size": 11.5, fill: "#fff", "font-weight": 600 }); t.textContent = (opt.prefix || "") + fmt(v, opt.digits ?? 0); svg.append(t); }
  return { x, y, W, H };
}
function candles(svg, n, start, seed, opt = {}) {
  fit(svg);
  const W = +svg.getAttribute("width"), H = +svg.getAttribute("height"), padR = 64, padB = 22; const r = rng(seed); let c = start; const bars = [];
  for (let i = 0; i < n; i++) { const o = c * (1 + (r() - .5) * .01); c = o * (1 + (r() - .48) * .03 + Math.sin(i / 14) * .004); const h = Math.max(o, c) * (1 + r() * .01), l = Math.min(o, c) * (1 - r() * .01); bars.push([o, h, l, c]); }
  const lo = Math.min(...bars.map(b => b[2])) * .99, hi = Math.max(...bars.map(b => b[1])) * 1.01; const y = scale([], lo, hi, 8, H - padB); const w = (W - padR) / n;
  for (let k = 0; k <= 4; k++) { const v = lo + (hi - lo) * k / 4, yy = y(v); svg.append(svgEl("line", { x1: 0, x2: W - padR, y1: yy, y2: yy, stroke: "#ECEDE5", "stroke-dasharray": "3 4" }));
    const t = svgEl("text", { x: W - padR + 10, y: yy + 4, "font-size": 11, fill: "#646E68" }); t.textContent = fmt(v); svg.append(t); }
  bars.forEach(([o, h, l, cl], i) => { const col = cl >= o ? "#C8343D" : "#2F6DB5", cx = i * w + w / 2;
    svg.append(svgEl("line", { x1: cx, x2: cx, y1: y(h), y2: y(l), stroke: col, "stroke-width": 1 }));
    svg.append(svgEl("rect", { x: cx - w * .32, y: y(Math.max(o, cl)), width: w * .64, height: Math.max(1, Math.abs(y(o) - y(cl))), fill: col })); });
  return bars;
}
function spark(svg, values, color) { fit(svg); const W = +svg.getAttribute("width"), H = +svg.getAttribute("height"); const lo = Math.min(...values), hi = Math.max(...values);
  const d = values.map((v, i) => `${i ? "L" : "M"}${(i / (values.length - 1) * W).toFixed(1)},${(H - 2 - (v - lo) / (hi - lo || 1) * (H - 4)).toFixed(1)}`).join("");
  svg.append(svgEl("path", { d, fill: "none", stroke: color, "stroke-width": 1.6 })); }
function bars(svg, values, opt = {}) { fit(svg); const W = +svg.getAttribute("width"), H = +svg.getAttribute("height"); const max = Math.max(...values.map(Math.abs)); const w = W / values.length; const mid = opt.signed ? H / 2 : H;
  values.forEach((v, i) => { const h = Math.abs(v) / max * (opt.signed ? H / 2 - 2 : H - 2); svg.append(svgEl("rect", { x: i * w + w * .18, y: v >= 0 ? mid - h : mid, width: w * .64, height: h, rx: 1.5, fill: opt.color ? opt.color(v, i) : (v >= 0 ? "#E8B4B6" : "#B5CBE6") })); }); }
