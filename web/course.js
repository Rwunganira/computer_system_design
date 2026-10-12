/* Shared engine for every lesson page: Python cells (Skulpt), a small pylab/numpy subset that draws charts,
   self-checking exercises, quick-check quizzes, flashcards, spaced-review dates and per-lesson progress. */
(function () {
"use strict";

const COURSE = [
  { id: "m00", part: 1, title: "Setup and the running case", blurb: "Meet SurveilLite and VaxRecords, the synthetic data, and what working means." },
  { id: "m01", part: 1, title: "Complexity", blurb: "Propagation of effects, incommensurate scaling, and the four ways to cope." },
  { id: "m02", part: 1, title: "Elements of computer systems", blurb: "Memory, interpreters and communication links, through a case-definition interpreter." },
  { id: "m03", part: 1, title: "Naming", blurb: "Names, contexts and resolution: patient identifiers across clinics." },
  { id: "m04", part: 1, title: "Clients and services", blurb: "Enforced modularity, remote procedure calls and safe retries." },
  { id: "m05", part: 1, title: "Virtualization", blurb: "Threads, race conditions, locks and bounded buffers." },
  { id: "m06", part: 1, title: "Performance", blurb: "Bottlenecks, batching, caching, concurrency and Little's law." },
  { id: "m07", part: 2, title: "Networks", blurb: "Best effort, the end-to-end argument and reliable SMS reporting." },
  { id: "m08", part: 2, title: "Fault tolerance", blurb: "Faults, errors and failures; checksums, redundancy and availability." },
  { id: "m09", part: 2, title: "Atomicity", blurb: "All-or-nothing dose recording with shadow copies, logs and two-phase commit." },
  { id: "m10", part: 2, title: "Consistency", blurb: "Offline tablets, last writer wins, version vectors and reconciliation." },
  { id: "m11", part: 2, title: "Information security", blurb: "Authentication, authorization, audit logs and the design principles." },
  { id: "m12", part: 2, title: "Capstone: a bad week", blurb: "Every failure at once, and the three checks that survive it." }
];

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const store = {
  get(k, d) { try { const v = localStorage.getItem("csd:" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem("csd:" + k, JSON.stringify(v)); } catch (e) {} }
};

/* ---------- syntax highlighting ---------- */
const KW = new Set("False None True and as assert break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield".split(" "));
const BI = new Set("print input len type int float str bool abs range round min max sum list dict tuple set sorted enumerate zip isinstance super self map filter".split(" "));
function highlight(src) {
  const re = /(#[^\n]*)|("""[\s\S]*?(?:"""|$)|'''[\s\S]*?(?:'''|$)|[rf]?"(?:[^"\\\n]|\\.)*"?|[rf]?'(?:[^'\\\n]|\\.)*'?)|\b(\d+\.?\d*(?:e[+-]?\d+)?)\b|\b([A-Za-z_]\w*)\b/g;
  let out = "", last = 0, m;
  while ((m = re.exec(src))) {
    out += esc(src.slice(last, m.index));
    if (m[1]) out += `<span class="c">${esc(m[1])}</span>`;
    else if (m[2]) out += `<span class="s">${esc(m[2])}</span>`;
    else if (m[3]) out += `<span class="n">${esc(m[3])}</span>`;
    else if (KW.has(m[4])) out += `<span class="k">${m[4]}</span>`;
    else if (BI.has(m[4])) out += `<span class="f">${m[4]}</span>`;
    else out += esc(m[4]);
    last = re.lastIndex;
  }
  return out + esc(src.slice(last)) + "\n";
}

/* ---------- pylab / numpy teaching subset (pure Python, runs inside Skulpt) ---------- */
const PYLAB = String.raw`
import math as _math

_fig = None
_COLORS = {'b': 1, 'r': 8, 'g': 6, 'c': 3, 'm': 5, 'y': 4, 'k': 0, 'o': 2, 'v': 7,
           'blue': 1, 'red': 8, 'green': 6, 'cyan': 3, 'magenta': 5, 'yellow': 4, 'black': 0, 'orange': 2, 'purple': 7, 'violet': 7}

def _new():
    return {'title': '', 'xlabel': '', 'ylabel': '', 'series': [], 'legend': False, 'xlim': None, 'ylim': None, 'logy': False, 'logx': False}

def _cur():
    global _fig
    if _fig is None:
        _fig = _new()
    return _fig

def _num(v):
    try:
        f = float(v)
    except Exception:
        return 'null'
    if f != f or f == float('inf') or f == float('-inf'):
        return 'null'
    return repr(f)

def _str(s):
    out = '"'
    for ch in str(s):
        if ch == '"' or ch == '\\':
            out += '\\' + ch
        elif ch == '\n':
            out += '\\n'
        else:
            out += ch
    return out + '"'

def _json(v):
    if v is None:
        return 'null'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, str):
        return _str(v)
    if isinstance(v, (list, tuple)):
        return '[' + ','.join([_json(x) for x in v]) + ']'
    if isinstance(v, dict):
        return '{' + ','.join([_str(k) + ':' + _json(v[k]) for k in v]) + '}'
    return _str(v)

def _parse_fmt(fmt):
    color = None
    marker = None
    dash = None
    if fmt:
        for ch in fmt:
            if ch in 'bgrcmyk':
                color = _COLORS[ch]
        if '--' in fmt:
            dash = 'dash'
        elif ':' in fmt:
            dash = 'dot'
        for mk in 'o.^sv*+x':
            if mk in fmt and not (mk == '.' and False):
                marker = mk
                break
        line = ('-' in fmt) or (':' in fmt)
    else:
        line = True
    return color, marker, dash, line

def _color(c):
    if c is None:
        return None
    if isinstance(c, int):
        return c
    return _COLORS.get(str(c).lower(), None)

def _list(v):
    if isinstance(v, (int, float)):
        return [v]
    return [x for x in v]

def plot(*args, **kw):
    a = list(args)
    fmt = None
    if len(a) > 0 and isinstance(a[-1], str):
        fmt = a.pop()
    if len(a) == 1:
        y = _list(a[0])
        x = list(range(len(y)))
    else:
        x = _list(a[0])
        y = _list(a[1])
    color, marker, dash, line = _parse_fmt(fmt)
    if 'color' in kw:
        color = _color(kw['color'])
    if 'c' in kw:
        color = _color(kw['c'])
    if 'linestyle' in kw:
        ls = kw['linestyle']
        dash = 'dash' if ls == '--' else ('dot' if ls == ':' else None)
        line = ls not in ('', 'None', 'none', ' ')
    if 'marker' in kw:
        marker = kw['marker']
    s = {'type': 'line' if line else 'scatter', 'x': x, 'y': y, 'label': kw.get('label', None),
         'color': color, 'dash': dash, 'marker': marker}
    _cur()['series'].append(s)
    return [s]

def scatter(x, y, s=None, c=None, color=None, label=None, marker='o', **kw):
    col = _color(color if color is not None else c)
    _cur()['series'].append({'type': 'scatter', 'x': _list(x), 'y': _list(y), 'label': label, 'color': col, 'marker': marker})

def bar(x, height, width=0.8, label=None, color=None, **kw):
    xs = _list(x)
    labels = None
    if len(xs) > 0 and isinstance(xs[0], str):
        labels = xs
        xs = list(range(len(xs)))
    _cur()['series'].append({'type': 'bar', 'x': xs, 'y': _list(height), 'width': width, 'label': label,
                             'color': _color(color), 'ticklabels': labels})

def hist(values, bins=10, label=None, color=None, weights=None, range=None, **kw):
    vals = _list(values)
    if len(vals) == 0:
        return [], [], None
    lo = min(vals) if range is None else range[0]
    hi = max(vals) if range is None else range[1]
    if hi == lo:
        hi = lo + 1
    n = int(bins)
    width = (hi - lo) / float(n)
    counts = [0] * n
    for i in _builtin_range(len(vals)):
        v = vals[i]
        if v < lo or v > hi:
            continue
        k = int((v - lo) / width)
        if k >= n:
            k = n - 1
        counts[k] += weights[i] if weights is not None else 1
    edges = [lo + width * i for i in _builtin_range(n + 1)]
    _cur()['series'].append({'type': 'bar', 'x': [lo + width * (i + 0.5) for i in _builtin_range(n)], 'y': counts,
                             'width': width, 'label': label, 'color': _color(color), 'ticklabels': None, 'hist': True})
    return counts, edges, None

_builtin_range = range

def axhline(y=0, color=None, linestyle='-', label=None, **kw):
    _cur()['series'].append({'type': 'hline', 'y': [y], 'x': [], 'color': _color(color), 'dash': 'dash' if linestyle == '--' else None, 'label': label})

def axvline(x=0, color=None, linestyle='-', label=None, **kw):
    _cur()['series'].append({'type': 'vline', 'x': [x], 'y': [], 'color': _color(color), 'dash': 'dash' if linestyle == '--' else None, 'label': label})

def title(t, **kw):
    _cur()['title'] = str(t)

def xlabel(t, **kw):
    _cur()['xlabel'] = str(t)

def ylabel(t, **kw):
    _cur()['ylabel'] = str(t)

def legend(*a, **kw):
    _cur()['legend'] = True

def xlim(lo=None, hi=None):
    if isinstance(lo, (list, tuple)):
        lo, hi = lo[0], lo[1]
    _cur()['xlim'] = [lo, hi]

def ylim(lo=None, hi=None):
    if isinstance(lo, (list, tuple)):
        lo, hi = lo[0], lo[1]
    _cur()['ylim'] = [lo, hi]

def semilogy(*args, **kw):
    _cur()['logy'] = True
    if len(args) > 0:
        plot(*args, **kw)

def semilogx(*args, **kw):
    _cur()['logx'] = True
    if len(args) > 0:
        plot(*args, **kw)

def yscale(s, **kw):
    _cur()['logy'] = (s == 'log')

def xscale(s, **kw):
    _cur()['logx'] = (s == 'log')

def grid(*a, **kw):
    pass

def xticks(*a, **kw):
    pass

def yticks(*a, **kw):
    pass

def rcParams(*a, **kw):
    pass

def figure(*a, **kw):
    global _fig
    if _fig is not None and len(_fig['series']) > 0:
        show()
    _fig = _new()

def show(*a, **kw):
    global _fig
    if _fig is not None and len(_fig['series']) > 0:
        print('\x01PLOT' + _json(_fig))
    _fig = None

savefig = show

def close(*a, **kw):
    global _fig
    _fig = None

# ---- numeric helpers (numpy-style names, plain lists) ----
def array(v):
    return [x for x in v]

def arange(a, b=None, step=1):
    if b is None:
        a, b = 0, a
    out = []
    x = a
    while (step > 0 and x < b) or (step < 0 and x > b):
        out.append(x)
        x += step
    return out

def linspace(a, b, n=50):
    if n == 1:
        return [float(a)]
    return [a + (b - a) * i / float(n - 1) for i in _builtin_range(n)]

def mean(v):
    v = _list(v)
    return sum(v) / float(len(v))

def var(v):
    v = _list(v)
    m = mean(v)
    return sum([(x - m) ** 2 for x in v]) / float(len(v))

def std(v):
    return var(v) ** 0.5

def median(v):
    s = sorted(_list(v))
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0

def sqrt(v):
    if isinstance(v, (list, tuple)):
        return [x ** 0.5 for x in v]
    return v ** 0.5

def polyval(p, x):
    if isinstance(x, (list, tuple)):
        return [polyval(p, xi) for xi in x]
    total = 0.0
    for c in p:
        total = total * x + c
    return total

def polyfit(x, y, deg):
    x = _list(x)
    y = _list(y)
    n = deg + 1
    A = [[0.0] * (n + 1) for i in _builtin_range(n)]
    for i in _builtin_range(n):
        for j in _builtin_range(n):
            A[i][j] = sum([xi ** (2 * deg - i - j) for xi in x])
        A[i][n] = sum([y[k] * x[k] ** (deg - i) for k in _builtin_range(len(x))])
    for col in _builtin_range(n):
        piv = col
        for r in _builtin_range(col + 1, n):
            if abs(A[r][col]) > abs(A[piv][col]):
                piv = r
        A[col], A[piv] = A[piv], A[col]
        if A[col][col] == 0:
            continue
        for r in _builtin_range(n):
            if r != col:
                f = A[r][col] / A[col][col]
                for c in _builtin_range(col, n + 1):
                    A[r][c] -= f * A[col][c]
    return [A[i][n] / A[i][i] if A[i][i] != 0 else 0.0 for i in _builtin_range(n)]

pi = _math.pi
e = _math.e
`;

/* ---------- Python runtime ---------- */
function readFile(x) {
  if (/(^|\/)(pylab|numpy)\.py$|matplotlib\/pyplot\.py$/.test(x)) return PYLAB;
  if (/matplotlib\/__init__\.py$/.test(x)) return "";
  if (Sk.builtinFiles === undefined || Sk.builtinFiles.files[x] === undefined) throw "File not found: '" + x + "'";
  return Sk.builtinFiles.files[x];
}
let queue = Promise.resolve();
let execLimit = 6000;
function runPython(code, { onOut, onInput, limit } = {}) {
  const job = () => new Promise(resolve => {
    if (typeof Sk === "undefined") { resolve({ out: "", error: "The Python interpreter could not load. Check your connection and reload the page." }); return; }
    let out = "";
    const lim = limit || execLimit;
    Sk.configure({
      output: t => { out += t; onOut && onOut(t); },
      read: readFile,
      __future__: Sk.python3,
      inputfunTakesPrompt: true,
      inputfun: p => onInput ? onInput(p) : Promise.resolve(""),
      execLimit: lim
    });
    Sk.misceval.asyncToPromise(() => Sk.importMainWithBody("<stdin>", false, code, true), { "*": () => {} })
      .then(() => resolve({ out, error: null }))
      .catch(e => {
        let msg = e.toString();
        if (/TimeLimitError|run time limit/i.test(msg)) msg = `Stopped after ${lim / 1000} seconds. Is there a loop that never ends, or a computation that is too large for the browser?`;
        resolve({ out, error: msg });
      });
  });
  queue = queue.then(job, job);
  return queue;
}
const textOnly = s => s.split("\n").filter(l => !l.startsWith("\x01PLOT")).join("\n");

/* ---------- charts ---------- */
const SERIES = n => n === 0 ? "var(--ink)" : `var(--s${n})`;
function niceTicks(lo, hi, count = 5) {
  if (!isFinite(lo) || !isFinite(hi)) return [0, 1];
  if (hi === lo) { hi = lo + 1; lo = lo - 1; }
  const span = hi - lo, raw = span / count, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => span / s <= count) || 10 * mag;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(+v.toPrecision(12));
  return out;
}
const tickFmt = v => { const a = Math.abs(v); if (a === 0) return "0"; if (a >= 1e6 || a < 1e-3) return v.toExponential(1); return String(+v.toPrecision(6)); };
function renderFigure(fig) {
  const W = 640, H = 340, L = fig.logy || fig.ylabel ? 72 : 58, R = 16, T = 12, B = 46;
  const wrap = document.createElement("div"); wrap.className = "fig";
  const series = fig.series;
  let colorIdx = 1;
  series.forEach(s => { if (s.color == null) { s.color = colorIdx; colorIdx = colorIdx % 8 + 1; } });
  const logy = fig.logy, logx = fig.logx;
  const tx = v => logx ? (v > 0 ? Math.log10(v) : NaN) : v, ty = v => logy ? (v > 0 ? Math.log10(v) : NaN) : v;
  let xs = [], ys = [];
  series.forEach(s => {
    if (s.type === "hline") ys.push(ty(s.y[0]));
    else if (s.type === "vline") xs.push(tx(s.x[0]));
    else {
      s.x.forEach((v, i) => { if (v != null && s.y[i] != null) { xs.push(tx(v)); ys.push(ty(s.y[i])); } });
      if (s.type === "bar") { const w = (s.width || 0.8) / 2; s.x.forEach(v => { xs.push(v - w, v + w); }); ys.push(0); }
    }
  });
  xs = xs.filter(isFinite); ys = ys.filter(isFinite);
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  if (!xs.length) { x0 = 0; x1 = 1; } if (!ys.length) { y0 = 0; y1 = 1; }
  if (fig.xlim) { if (fig.xlim[0] != null) x0 = tx(fig.xlim[0]); if (fig.xlim[1] != null) x1 = tx(fig.xlim[1]); }
  if (fig.ylim) { if (fig.ylim[0] != null) y0 = ty(fig.ylim[0]); if (fig.ylim[1] != null) y1 = ty(fig.ylim[1]); }
  const hasBar = series.some(s => s.type === "bar");
  if (!fig.xlim && !hasBar && !logx) { const px = (x1 - x0) * 0.03; x0 -= px; x1 += px; }
  if (!fig.ylim && !logy) { const py = (y1 - y0) * 0.04; if (!(hasBar && y0 >= 0)) y0 -= py; y1 += py; }
  if (x1 === x0) { x0 -= 1; x1 += 1; }
  if (y1 === y0) { y0 -= 1; y1 += 1; }
  const yt = logy ? niceTicks(Math.floor(y0), Math.ceil(y1)).filter(Number.isInteger) : niceTicks(y0, y1);
  const xt = logx ? niceTicks(Math.floor(x0), Math.ceil(x1)).filter(Number.isInteger) : niceTicks(x0, x1, 6);
  if (!fig.ylim) { y0 = Math.min(y0, yt[0]); y1 = Math.max(y1, yt[yt.length - 1]); }
  if (!fig.xlim && !hasBar) { x0 = Math.min(x0, xt[0]); x1 = Math.max(x1, xt[xt.length - 1]); }
  const sx = v => L + (tx(v) - x0) / (x1 - x0) * (W - L - R);
  const sy = v => T + (1 - (ty(v) - y0) / (y1 - y0)) * (H - T - B);
  const sxr = v => L + (v - x0) / (x1 - x0) * (W - L - R), syr = v => T + (1 - (v - y0) / (y1 - y0)) * (H - T - B);
  let g = "";
  yt.forEach(v => { if (v < y0 - 1e-9 || v > y1 + 1e-9) return; const y = syr(v); g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="var(--chart-grid)"/><text x="${L - 8}" y="${y + 4}" text-anchor="end">${logy ? tickFmt(Math.pow(10, v)) : tickFmt(v)}</text>`; });
  const barLabels = series.find(s => s.type === "bar" && s.ticklabels);
  if (barLabels) barLabels.ticklabels.forEach((t, i) => { g += `<text x="${sxr(i)}" y="${H - B + 18}" text-anchor="middle">${esc(String(t).slice(0, 12))}</text>`; });
  else xt.forEach(v => { if (v < x0 - 1e-9 || v > x1 + 1e-9) return; g += `<text x="${sxr(v)}" y="${H - B + 18}" text-anchor="middle">${logx ? tickFmt(Math.pow(10, v)) : tickFmt(v)}</text>`; });
  g += `<line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" stroke="var(--chart-axis)"/>`;
  const pts = [];
  const clipId = "clip" + Math.random().toString(36).slice(2);
  let marks = "";
  series.forEach(s => {
    const col = SERIES(s.color), dash = s.dash === "dash" ? ' stroke-dasharray="6 4"' : s.dash === "dot" ? ' stroke-dasharray="2 4"' : "";
    if (s.type === "line") {
      let d = "", pen = false;
      s.x.forEach((v, i) => { const X = sx(v), Y = sy(s.y[i]); if (!isFinite(X) || !isFinite(Y)) { pen = false; return; } d += (pen ? "L" : "M") + X.toFixed(1) + "," + Y.toFixed(1); pen = true; pts.push([X, Y, v, s.y[i], s.label]); });
      marks += `<path d="${d}" fill="none" stroke="${col}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"${dash}/>`;
      if (s.marker && s.x.length <= 400) s.x.forEach((v, i) => { const X = sx(v), Y = sy(s.y[i]); if (isFinite(X) && isFinite(Y)) marks += `<circle cx="${X.toFixed(1)}" cy="${Y.toFixed(1)}" r="3.5" fill="${col}" stroke="var(--sheet)" stroke-width="1.5"/>`; });
    } else if (s.type === "scatter") {
      const step = Math.max(1, Math.ceil(s.x.length / 3000));
      for (let i = 0; i < s.x.length; i += step) { const X = sx(s.x[i]), Y = sy(s.y[i]); if (!isFinite(X) || !isFinite(Y)) continue; marks += `<circle cx="${X.toFixed(1)}" cy="${Y.toFixed(1)}" r="${s.x.length > 500 ? 2.5 : 4}" fill="${col}" fill-opacity="0.85" stroke="var(--sheet)" stroke-width="1"/>`; pts.push([X, Y, s.x[i], s.y[i], s.label]); }
    } else if (s.type === "bar") {
      const w = (s.width || 0.8);
      s.x.forEach((v, i) => {
        const a = sxr(v - w / 2), b = sxr(v + w / 2), top = syr(Math.max(0, s.y[i])), base = syr(Math.max(y0, Math.min(0, s.y[i]) || 0));
        const bw = Math.max(1, b - a - 2), h = Math.max(0, Math.abs(base - top));
        const r = Math.min(4, bw / 2, h);
        marks += `<path d="M${a + 1},${base} V${top + r} q0,-${r} ${r},-${r} H${a + 1 + bw - r} q${r},0 ${r},${r} V${base} Z" fill="${col}"/>`;
        pts.push([(a + b) / 2, top, s.ticklabels ? s.ticklabels[i] : v, s.y[i], s.label]);
      });
    } else if (s.type === "hline") {
      const Y = sy(s.y[0]); marks += `<line x1="${L}" x2="${W - R}" y1="${Y}" y2="${Y}" stroke="${col}" stroke-width="1.5"${dash || ' stroke-dasharray="6 4"'}/>`;
    } else if (s.type === "vline") {
      const X = sx(s.x[0]); marks += `<line x1="${X}" x2="${X}" y1="${T}" y2="${H - B}" stroke="${col}" stroke-width="1.5"${dash || ' stroke-dasharray="6 4"'}/>`;
    }
  });
  g += `<clipPath id="${clipId}"><rect x="${L}" y="${T - 4}" width="${W - L - R}" height="${H - T - B + 4}"/></clipPath><g clip-path="url(#${clipId})">${marks}</g>`;
  if (fig.xlabel) g += `<text class="axis-label" x="${(L + W - R) / 2}" y="${H - 8}" text-anchor="middle">${esc(fig.xlabel)}</text>`;
  if (fig.ylabel) g += `<text class="axis-label" transform="translate(14 ${(T + H - B) / 2}) rotate(-90)" text-anchor="middle">${esc(fig.ylabel)}</text>`;
  const labeled = series.filter(s => s.label);
  const legend = (fig.legend || labeled.length > 1) && labeled.length ? `<div class="fig-legend">${labeled.map(s => `<span><i class="${s.type === "scatter" ? "dot" : ""}" style="background:${SERIES(s.color)}"></i>${esc(s.label)}</span>`).join("")}</div>` : "";
  wrap.innerHTML = `${fig.title ? `<div class="fig-title">${esc(fig.title)}</div>` : ""}${legend}<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(fig.title || "chart")}">${g}</svg><div class="tip" hidden></div>`;
  const svg = $("svg", wrap), tip = $(".tip", wrap);
  svg.addEventListener("mousemove", e => {
    if (!pts.length) return;
    const r = svg.getBoundingClientRect(), k = W / r.width, mx = (e.clientX - r.left) * k, my = (e.clientY - r.top) * k;
    let best = null, bd = 1e9;
    for (const p of pts) { const d = (p[0] - mx) ** 2 + (p[1] - my) ** 2; if (d < bd) { bd = d; best = p; } }
    if (!best || bd > 1600) { tip.hidden = true; return; }
    tip.hidden = false;
    tip.textContent = `${best[4] ? best[4] + " · " : ""}${typeof best[2] === "number" ? tickFmt(best[2]) : best[2]}, ${tickFmt(best[3])}`;
    tip.style.left = (best[0] / k + (svg.offsetLeft)) + "px"; tip.style.top = (best[1] / k + svg.offsetTop) + "px";
  });
  svg.addEventListener("mouseleave", () => { tip.hidden = true; });
  return wrap;
}

/* ---------- code cells ---------- */
function makeWriter(o) {
  let started = false, pending = "";
  const raw = t => { if (!started) { o.textContent = ""; started = true; } o.appendChild(document.createTextNode(t)); };
  const flushLine = line => {
    if (line.startsWith("\x01PLOT")) { if (!started) { o.textContent = ""; started = true; } try { o.appendChild(renderFigure(JSON.parse(line.slice(5)))); } catch (e) { raw("[could not draw chart: " + e.message + "]\n"); } }
    else raw(line + "\n");
  };
  return {
    write(t) { pending += t; let i; while ((i = pending.indexOf("\n")) >= 0) { flushLine(pending.slice(0, i)); pending = pending.slice(i + 1); } },
    flush() { if (pending) { raw(pending); pending = ""; } },
    get started() { return started; }
  };
}
function setupCell(cell) {
  const ta = $("textarea", cell), pre = $("pre", cell);
  let bar = $(".cell-bar", cell);
  if (!bar) { bar = document.createElement("div"); bar.className = "cell-bar"; bar.innerHTML = `<button class="run" type="button">Run ▸</button><button class="btn-ghost reset" type="button">Reset</button><span class="hint">Ctrl + Enter runs</span>`; $(".ed", cell).after(bar); }
  const original = ta.value;
  const key = "code:" + LID + ":" + ta.id;
  const saved = store.get(key, null);
  if (saved != null) ta.value = saved;
  const sync = () => { pre.innerHTML = highlight(ta.value); };
  sync();
  ta.addEventListener("input", () => { sync(); store.set(key, ta.value); });
  ta.addEventListener("keydown", e => {
    if (e.key === "Tab" && !e.shiftKey) {
      e.preventDefault();
      const s = ta.selectionStart, en = ta.selectionEnd;
      ta.value = ta.value.slice(0, s) + "    " + ta.value.slice(en);
      ta.selectionStart = ta.selectionEnd = s + 4; ta.dispatchEvent(new Event("input"));
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault(); run();
    } else if (e.key === "Enter") {
      const s = ta.selectionStart;
      const lineStart = ta.value.lastIndexOf("\n", s - 1) + 1;
      const line = ta.value.slice(lineStart, s);
      let ind = (line.match(/^\s*/) || [""])[0];
      if (/:\s*$/.test(line)) ind += "    ";
      if (ind) {
        e.preventDefault();
        ta.value = ta.value.slice(0, s) + "\n" + ind + ta.value.slice(ta.selectionEnd);
        ta.selectionStart = ta.selectionEnd = s + 1 + ind.length; ta.dispatchEvent(new Event("input"));
      }
    }
  });
  let outEl = null, verdictEl = null;
  const ensureOut = () => {
    if (!outEl) { outEl = document.createElement("div"); outEl.className = "out"; outEl.setAttribute("aria-live", "polite"); bar.after(outEl); }
    return outEl;
  };
  const setVerdict = (cls, html) => {
    if (!verdictEl) { verdictEl = document.createElement("div"); cell.appendChild(verdictEl); }
    verdictEl.className = "verdict " + cls; verdictEl.innerHTML = html;
  };
  const runBtn = $(".run", bar);
  async function run() {
    const o = ensureOut(); o.innerHTML = '<span class="sys">Running…</span>';
    if (verdictEl && !cell.dataset.exercise) { verdictEl.remove(); verdictEl = null; }
    runBtn.disabled = true;
    const w = makeWriter(o);
    const res = await runPython(ta.value, {
      limit: cell.dataset.limit ? +cell.dataset.limit : undefined,
      onOut: t => w.write(t),
      onInput: p => new Promise(resolve => {
        w.write(p); w.flush();
        const row = document.createElement("div"); row.className = "in-row";
        const id = ta.id + "-in";
        row.innerHTML = `<label class="sys" for="${id}">your input</label><input id="${id}" autocomplete="off"><button class="btn-ghost" type="button">Enter</button>`;
        o.appendChild(row);
        const inp = $("input", row); inp.focus();
        const done = () => { const v = inp.value; row.remove(); w.write(v + "\n"); resolve(v); };
        inp.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); done(); } });
        $("button", row).addEventListener("click", done);
      })
    });
    w.flush();
    runBtn.disabled = false;
    if (!w.started) o.textContent = "";
    if (res.error) { const sp = document.createElement("span"); sp.className = "err"; sp.textContent = (res.out ? "\n" : "") + res.error; o.appendChild(sp); }
    else if (!res.out) o.innerHTML = '<span class="sys">(ran with no output)</span>';
    if (cell.dataset.predict != null && $(".predict input", cell)) {
      const guess = ($(".predict input", cell).value || "").trim();
      const lines = textOnly(res.out).trim().split("\n");
      const actual = lines[lines.length - 1].trim();
      if (!guess) setVerdict("no", "No prediction this time. Predicting first is the fastest way to find gaps in your model.");
      else if (guess.replace(/['"\s]/g, "").toLowerCase() === actual.replace(/['"\s]/g, "").toLowerCase()) setVerdict("yes", "Your prediction matched: <b>" + esc(actual) + "</b>");
      else setVerdict("no", "You predicted <b>" + esc(guess) + "</b>; Python printed <b>" + esc(actual) + "</b>. Find the line that surprised you.");
    }
    return res;
  }
  runBtn.addEventListener("click", run);
  $(".reset", bar).addEventListener("click", () => { ta.value = original; sync(); store.set(key, null); if (outEl) { outEl.remove(); outEl = null; } if (verdictEl) { verdictEl.remove(); verdictEl = null; } });
  cell._setVerdict = setVerdict; cell._ta = ta; cell._bar = bar; cell._run = run;
}

/* ---------- exercises ---------- */
const MARK = "\n___CASE___";
function buildCase(src, c) {
  if (typeof c === "string") return src + "\nprint(" + JSON.stringify(MARK.trim()) + ")\n" + c + "\n";
  let s = src;
  Object.entries(c).forEach(([k, v]) => {
    const re = new RegExp("^(\\s*)" + k + "\\s*=.*$", "m");
    const val = typeof v === "string" ? v : JSON.stringify(v).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False").replace(/\bnull\b/g, "None");
    s = re.test(s) ? s.replace(re, "$1" + k + " = " + val) : k + " = " + val + "\n" + s;
  });
  return s;
}
function caseOutput(res, c) {
  if (res.error) return { err: res.error.split("\n").pop() };
  let out = textOnly(res.out);
  if (typeof c === "string") { const i = out.indexOf(MARK.trim()); out = i >= 0 ? out.slice(i + MARK.trim().length) : ""; }
  return { out: out.trim().split("\n").map(l => l.trimEnd()).join("\n") };
}
function caseLabel(c) { return typeof c === "string" ? c.trim().split("\n").join("; ") : Object.entries(c).map(([k, v]) => `${k} = ${typeof v === "string" ? v : JSON.stringify(v)}`).join(", "); }
function setupExercise(cell, ex, id) {
  const bar = cell._bar;
  $(".hint", bar) && $(".hint", bar).remove();
  const check = document.createElement("button"); check.className = "btn-ghost"; check.type = "button"; check.textContent = "Check my answer";
  const hint = document.createElement("button"); hint.className = "btn-ghost"; hint.type = "button"; hint.textContent = "Show a hint";
  const sol = document.createElement("button"); sol.className = "btn-ghost"; sol.type = "button"; sol.textContent = "Show solution"; sol.hidden = true;
  $(".run", bar).after(check, hint, sol);
  let hintsShown = 0, fails = 0;
  const hints = Array.isArray(ex.hint) ? ex.hint : [ex.hint];
  hint.addEventListener("click", () => {
    cell._setVerdict("no", "Hint " + (hintsShown + 1) + " of " + hints.length + ": " + esc(hints[Math.min(hintsShown, hints.length - 1)]));
    hintsShown = Math.min(hintsShown + 1, hints.length - 1);
  });
  sol.addEventListener("click", () => {
    cell._setVerdict("no", "One possible solution. Read it, close it, then type your own version from memory:<pre style=\"margin:8px 0 0;white-space:pre-wrap;color:var(--code-fg)\">" + highlight(ex.solution).trimEnd() + "</pre>");
  });
  check.addEventListener("click", async () => {
    cell._setVerdict("no", "Checking…"); check.disabled = true;
    let passed = 0, first = null;
    for (const c of ex.cases) {
      const want = caseOutput(await runPython(buildCase(ex.solution, c), { limit: ex.limit }), c);
      const got = caseOutput(await runPython(buildCase(cell._ta.value, c), { limit: ex.limit }), c);
      const ok = !got.err && got.out === want.out;
      if (ok) passed++; else if (!first) first = { c, want, got };
    }
    check.disabled = false;
    if (!first) {
      cell._setVerdict("yes", `All ${passed} test cases pass. Nicely done.`);
      const done = store.get("ex:" + LID, {}); done[id] = true; store.set("ex:" + LID, done); updateProgress();
    } else {
      fails++; if (fails >= 2) sol.hidden = false;
      const shown = first.got.err ? "an error: " + first.got.err : (first.got.out || "(nothing)");
      cell._setVerdict("no", `${passed} of ${ex.cases.length} cases pass. For <b>${esc(caseLabel(first.c))}</b> the expected output is <b>${esc(first.want.out || first.want.err)}</b> but your code gave <b>${esc(shown)}</b>.`);
    }
  });
}

/* ---------- quizzes ---------- */
function renderQuiz(host, items) {
  const key = host.dataset.quiz;
  const solved = store.get("solved:" + LID, {});
  host.innerHTML = `<span class="tag check" style="justify-self:start">Quick check</span>`;
  items.forEach((it, qi) => {
    const id = `${key}-${qi}`;
    const el = document.createElement("div"); el.className = "q";
    el.innerHTML = `<div class="q-text">${it.q}</div>${it.code ? `<pre>${highlight(it.code).trimEnd()}</pre>` : ""}<div class="opts">${it.o.map((o, j) => `<button class="opt" type="button" data-j="${j}"><span class="key">${"ABCDEF"[j]}</span><span>${o}</span></button>`).join("")}</div>`;
    host.appendChild(el);
    const showWhy = ok => { let w = $(".why", el); if (!w) { w = document.createElement("div"); el.appendChild(w); } w.className = "why " + (ok ? "ok" : "no"); w.innerHTML = ok ? "<b>Correct.</b> " + it.why : "<b>Not quite.</b> Try another option."; };
    $$(".opt", el).forEach(b => b.addEventListener("click", () => {
      const j = +b.dataset.j;
      if (j === it.a) { b.classList.add("right"); $$(".opt", el).forEach(x => x.disabled = true); showWhy(true); const s = store.get("solved:" + LID, {}); s[id] = true; store.set("solved:" + LID, s); updateProgress(); }
      else { b.classList.add("wrong"); b.disabled = true; showWhy(false); }
    }));
    if (solved[id]) { const b = $(`.opt[data-j="${it.a}"]`, el); b.classList.add("right"); $$(".opt", el).forEach(x => x.disabled = true); showWhy(true); }
  });
}

/* ---------- flashcards + schedule ---------- */
function renderDeck(host, cards) {
  host.innerHTML = `<div class="card" tabindex="0" role="button" aria-label="Flashcard, press to flip"><div class="card-in"><div class="face front"></div><div class="face back"></div></div></div>
  <div class="deck-bar"><button class="btn alt" data-act="again" type="button">Again</button><button class="btn" data-act="got" type="button">Got it</button><button class="btn alt" data-act="restart" type="button">Shuffle and restart</button><span class="count"></span></div>`;
  const card = $(".card", host), front = $(".front", host), back = $(".back", host), count = $(".count", host);
  const got = $('[data-act="got"]', host), again = $('[data-act="again"]', host);
  let deck = [], seen = 0;
  const start = () => { deck = cards.map((_, i) => i).sort(() => Math.random() - 0.5); seen = 0; show(); };
  const show = () => {
    card.classList.remove("flipped");
    if (!deck.length) { front.innerHTML = "<small>Deck complete</small>Every card recalled."; back.innerHTML = "Shuffle and restart to go again."; count.textContent = `${cards.length} of ${cards.length} recalled`; got.disabled = again.disabled = true; return; }
    got.disabled = again.disabled = false;
    const [f, b] = cards[deck[0]];
    front.innerHTML = `<small>Recall · tap to flip</small>${f}`;
    setTimeout(() => { back.innerHTML = `<small>Answer</small>${b}`; }, reduced ? 0 : 200);
    count.textContent = `${seen} of ${cards.length} recalled · ${deck.length} left`;
  };
  const flip = () => card.classList.toggle("flipped");
  card.addEventListener("click", flip);
  card.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); flip(); } });
  got.addEventListener("click", () => { deck.shift(); seen++; show(); });
  again.addEventListener("click", () => { deck.push(deck.shift()); show(); });
  $('[data-act="restart"]', host).addEventListener("click", start);
  start();
}
function renderSchedule(host) {
  const startAt = store.get("finished:" + LID, null) || Date.now();
  const day = 86400000, f = d => new Date(startAt + d * day).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  host.innerHTML = [[1, "Tomorrow"], [3, "In 3 days"], [7, "In a week"], [21, "In 3 weeks"]].map(([d, l]) => `<div><b>${l}</b><span>${f(d)}</span></div>`).join("");
}

/* ---------- rail, progress, navigation ---------- */
let LID = null, CFG = null;
function buildRail() {
  const rail = $(".rail");
  const idx = COURSE.findIndex(l => l.id === LID), L = COURSE[idx] || { title: document.title, part: 1 };
  const secs = $$("section.lesson[id]");
  rail.innerHTML = `<a class="home" href="index.html">← Course home</a>
    <div class="brand">${esc(L.title)}<small>${L.part === 1 ? "Part I · Foundations" : "Part II · Distributed and reliable"} · Module ${idx} of ${COURSE.length - 1}</small></div>
    <div class="meter"><div class="meter-bar"><span id="meter-fill"></span></div><div class="meter-label" id="meter-label"></div></div>
    <ol class="toc">${secs.map((s, i) => `<li><a href="#${s.id}" data-sec="${s.id}"><span class="tick">${String(i + 1).padStart(2, "0")}</span><span>${esc(s.dataset.short || $("h2", s).textContent)}</span></a></li>`).join("")}</ol>`;
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) $$(".toc a", rail).forEach(a => a.classList.toggle("active", a.dataset.sec === e.target.id)); }), { rootMargin: "-30% 0px -60% 0px" });
  secs.forEach(s => io.observe(s));
  const main = $("main"), foot = $("main footer");
  const nav = document.createElement("nav"); nav.className = "lesson-nav"; nav.setAttribute("aria-label", "Lesson navigation");
  const prev = COURSE[idx - 1], next = COURSE[idx + 1];
  nav.innerHTML = (prev ? `<a href="${prev.id}.html"><span>← Module ${idx - 1}</span><b>${esc(prev.title)}</b></a>` : "") + (next ? `<a class="next-l" href="${next.id}.html"><span>Module ${idx + 1} →</span><b>${esc(next.title)}</b></a>` : `<a class="next-l" href="index.html"><span>Finished →</span><b>Back to the course map</b></a>`);
  foot ? main.insertBefore(nav, foot) : main.appendChild(nav);
}
function updateProgress() {
  const solved = store.get("solved:" + LID, {}), ex = store.get("ex:" + LID, {});
  const qs = Object.keys(CFG.quiz || {});
  const doneQ = qs.filter(s => CFG.quiz[s].every((_, i) => solved[`${s}-${i}`]));
  const exIds = Object.keys(CFG.exercises || {}), doneEx = exIds.filter(i => ex[i]);
  const total = qs.length + exIds.length, done = doneQ.length + doneEx.length;
  const fill = $("#meter-fill"); if (fill) fill.style.width = (total ? done / total * 100 : 0) + "%";
  const lab = $("#meter-label"); if (lab) lab.textContent = `${doneQ.length} of ${qs.length} checks · ${doneEx.length} of ${exIds.length} programs`;
  $$(".toc a").forEach(a => { const s = a.dataset.sec; const d = qs.includes(s) && doneQ.includes(s); a.classList.toggle("done", d); if (d) $(".tick", a).textContent = "✓"; });
  const all = store.get("progress", {}); all[LID] = { done, total, at: Date.now() }; store.set("progress", all);
  if (total && done === total && !store.get("finished:" + LID, null)) { store.set("finished:" + LID, Date.now()); const sh = $("#schedule"); if (sh) renderSchedule(sh); }
}

function lesson(cfg) {
  CFG = cfg; LID = document.body.dataset.lesson;
  if (cfg.execLimit) execLimit = cfg.execLimit;
  buildRail();
  $$(".cell").forEach(setupCell);
  Object.entries(cfg.exercises || {}).forEach(([id, ex]) => { const cell = document.getElementById(id); if (cell) setupExercise(cell, ex, id); else console.warn("missing exercise cell", id); });
  $$(".quiz[data-quiz]").forEach(h => { const items = (cfg.quiz || {})[h.dataset.quiz]; if (items) renderQuiz(h, items); else console.warn("missing quiz", h.dataset.quiz); });
  const deck = $(".deck-host"); if (deck && cfg.cards) renderDeck(deck, cfg.cards);
  const sh = $("#schedule"); if (sh) renderSchedule(sh);
  updateProgress();
}

window.CT = { COURSE, lesson, highlight, runPython, renderFigure, esc, $, $$, store, reduced };
})();
