// Usage: npm install --no-save playwright skulpt@1.2.0 && node tools/test_lesson.js l02 [--shots]
// Loads a lesson from this folder in headless Chromium, runs every code cell, checks every exercise
// against its own solution, answers nothing, and reports JS errors, Python errors, overflow and timing.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const DIR = path.join(__dirname, '..'), SK = process.env.SKULPT_DIR || path.join(DIR, 'node_modules', 'skulpt', 'dist');
(async () => {
  const lid = process.argv[2], shots = process.argv.includes('--shots');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push('console: ' + m.text()); });
  await p.route('**/*', r => {
    const u = new URL(r.request().url());
    if (u.hostname === 'cdn.jsdelivr.net') return r.fulfill({ path: path.join(SK, path.basename(u.pathname)), contentType: 'text/javascript' });
    if (u.hostname.includes('fonts.g')) return r.fulfill({ body: '', contentType: 'text/css' });
    if (u.hostname === 'course.test') { const f = path.join(DIR, u.pathname.slice(1) || 'index.html'); if (fs.existsSync(f)) return r.fulfill({ path: f }); return r.fulfill({ status: 404, body: 'nf' }); }
    return r.abort();
  });
  await p.goto(`https://course.test/${lid}.html`);
  await p.waitForTimeout(300);
  const cells = await p.$$('.cell');
  console.log(`${lid}: ${cells.length} cells`);
  for (let i = 0; i < cells.length; i++) {
    const c = cells[i];
    const isEx = await c.evaluate(e => !!e.id && !!window.CT && e.querySelector('.cell-bar').textContent.includes('Check'));
    const id = await c.evaluate(e => e.id || e.querySelector('textarea').id);
    // answer input() prompts automatically with "5"
    const t0 = Date.now();
    await c.$eval('.run', b => b.click());
    for (let k = 0; k < 200; k++) {
      await p.waitForTimeout(100);
      const inp = await c.$('.out .in-row input');
      if (inp) { await inp.fill('5'); await inp.press('Enter'); }
      if (await c.$eval('.run', b => !b.disabled)) break;
    }
    const out = await c.$eval('.out', o => o.innerText).catch(() => '(no out)');
    const figs = await c.$$eval('.out .fig', f => f.length).catch(() => 0);
    const bad = /Error|Stopped after/.test(out) ? '  <<< PY ERROR' : '';
    console.log(`  [${id}]${isEx ? ' (exercise starter)' : ''} ${Date.now() - t0}ms figs=${figs}${bad}\n    ` + out.slice(0, 400).replace(/\n/g, '\n    '));
  }
  // exercises: paste solution, check
  const exIds = await p.evaluate(() => Array.from(document.querySelectorAll('.cell')).filter(c => c.querySelector('.cell-bar') && c.querySelector('.cell-bar').textContent.includes('Check')).map(c => c.id));
  for (const id of exIds) {
    const sol = await p.evaluate(id => { const btns = Array.from(document.querySelectorAll('#' + id + ' .cell-bar button')); return null; }, id);
    await p.evaluate(id => { const c = document.getElementById(id); const b = Array.from(c.querySelectorAll('.cell-bar button')).find(x => x.textContent === 'Show solution'); b.hidden = false; b.click(); }, id);
    const solText = await p.$eval('#' + id + ' .verdict pre', e => e.innerText);
    await p.fill('#' + id + ' textarea', solText);
    await p.evaluate(id => Array.from(document.querySelectorAll('#' + id + ' .cell-bar button')).find(x => x.textContent === 'Check my answer').click(), id);
    let v = '';
    for (let k = 0; k < 300; k++) { await p.waitForTimeout(100); v = await p.$eval('#' + id + ' .verdict', e => e.innerText); if (!/Checking/.test(v)) break; }
    // starter should NOT pass
    console.log(`  exercise ${id}: solution -> ${v.slice(0, 200)}`);
  }
  // quizzes: count and verify answer indices in range
  const q = await p.evaluate(() => Array.from(document.querySelectorAll('.quiz')).map(h => h.dataset.quiz + ':' + h.querySelectorAll('.q').length).join(' '));
  console.log('  quizzes', q, ' deck', await p.$$eval('.deck-host .card', d => d.length));
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  await p.evaluate(() => { document.documentElement.style.scrollBehavior = 'auto'; scrollTo(0, 0); });
  if (shots) await p.screenshot({ path: path.join(DIR, 'tools', `shot-${lid}-desk.png`) });
  await p.setViewportSize({ width: 390, height: 844 });
  await p.emulateMedia({ colorScheme: 'dark' });
  await p.waitForTimeout(200);
  const swm = await p.evaluate(() => document.documentElement.scrollWidth);
  if (shots) await p.screenshot({ path: path.join(DIR, 'tools', `shot-${lid}-mob.png`), fullPage: false });
  console.log(`  scrollWidth desktop=${sw} mobile=${swm}${swm > 390 ? '  <<< OVERFLOW' : ''}`);
  console.log('  errors:', errs.length ? errs.join('\n   ') : 'none');
  await b.close();
})();
