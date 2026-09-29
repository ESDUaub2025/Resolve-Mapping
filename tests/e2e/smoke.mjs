// End-to-end smoke test of the public map in headless Chrome.
//   node tests/e2e/smoke.mjs            (needs Chrome and the Python venv; no private data)
// Env: CHROME=<path to chrome>, PYTHON=<python executable>. Exits non-zero on failure.
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.CHROME || ['C:/Program Files/Google/Chrome/Application/chrome.exe', '/usr/bin/google-chrome', '/usr/bin/chromium']
	.find(existsSync);
const PYTHON = process.env.PYTHON || (existsSync('.venv/Scripts/python.exe') ? '.venv/Scripts/python.exe' : 'python');
const HTTP_PORT = 8790 + Math.floor(Math.random() * 100);
const CDP_PORT = 9400 + Math.floor(Math.random() * 400);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const failures = [];
const expect = (cond, msg) => { if (!cond) failures.push(msg); };

setTimeout(() => { console.error('timeout'); cleanup(3); }, 120000);
const server = spawn(PYTHON, ['-m', 'resolve', 'serve', '--tier', 'public', '--port', String(HTTP_PORT)], { stdio: 'ignore' });
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'resolve-e2e-'))}`,
	'--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--window-size=1280,850', 'about:blank'], { stdio: 'ignore' });
function cleanup(code) { try { chrome.kill(); server.kill(); } catch { /* ignore */ } process.exit(code); }

let ws;
for (let i = 0; i < 60 && !ws; i++) {
	try {
		const page = (await (await fetch(`http://127.0.0.1:${CDP_PORT}/json`)).json()).find(t => t.type === 'page');
		if (page) ws = new WebSocket(page.webSocketDebuggerUrl);
	} catch { /* not up yet */ }
	await sleep(250);
}
if (ws.readyState !== 1) await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map(); const errors = []; const httpFailures = [];
ws.addEventListener('message', ev => {
	const m = JSON.parse(ev.data);
	if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); return; }
	if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map(a => a.value ?? a.description).join(' '));
	if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
	if (m.method === 'Network.responseReceived' && m.params.response.status >= 400 && m.params.response.url.includes('127.0.0.1')) httpFailures.push(m.params.response.url);
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const js = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.result.value;
await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');
await sleep(1500);
await send('Page.navigate', { url: `http://127.0.0.1:${HTTP_PORT}/` });
await sleep(10000);

const layers = await js(`document.querySelectorAll('.layer').length`);
expect(layers >= 4, `expected >= 4 layers, got ${layers}`);
expect(await js(`document.querySelector('.layer-controls select')?.options.length`) > 10, 'indicator selector missing');
expect(await js(`document.querySelectorAll('.legend li').length`) >= 3, 'legend missing');
expect(await js(`document.getElementById('tier-banner').hidden`) === true, 'public site must not show the research banner');

const openList = async (titlePart) => {
	await js(`[...document.querySelectorAll('.layer')].find(l => l.querySelector('.check span').textContent.toLowerCase().includes('${titlePart}'))
		?.querySelector('.layer-head .icon-btn:last-child').click()`);
	await sleep(500);
	await js(`document.querySelector('.place-list .link-btn').click()`);
	await sleep(1000);
};

// Village summary: distributions and location precision.
await openList('village');
expect(await js(`document.querySelectorAll('.details-body .indicator').length`) > 5, 'survey summary did not render indicators');
expect(/Cadastral/.test(await js(`document.querySelector('.details-body .precision')?.textContent || ''`)), 'location precision not shown');

// Respondent pin: ID title, approximate-position note, answers, and no identity block.
await openList('respondents');
expect(/Respondent (CH|BQ)-/.test(await js(`document.getElementById('details-title').textContent`)), 'pin popup has no ID');
expect(await js(`document.querySelectorAll('.details-body .props .row').length`) > 10, 'pin popup shows too few answers');
expect(await js(`document.querySelector('.details-body .identity') === null`), 'public pin shows an identity block');

// Pin filters change the number of pins shown.
const before = await js(`document.querySelector('[id^=count-]')?.textContent || ''`);
await js(`(() => { const s = [...document.querySelectorAll('.filters select')][0]; s.selectedIndex = 1; s.dispatchEvent(new Event('change')); })()`);
await sleep(600);
const after = await js(`document.querySelector('[id^=count-]')?.textContent || ''`);
expect(before && after && before !== after, `pin filter did not change the count (${before} -> ${after})`);

// Insights: farmer types and driver findings.
await js(`document.getElementById('open-insights').click()`);
await sleep(600);
expect(await js(`document.querySelectorAll('.insight-card').length`) >= 2, 'insights: farmer types missing');
expect(await js(`document.querySelectorAll('.findings li').length`) >= 1, 'insights: findings missing');

await js(`document.getElementById('toggle-lang').click()`);
await sleep(500);
expect(await js(`document.documentElement.dir`) === 'rtl', 'Arabic did not switch to RTL');
expect(errors.length === 0, `console errors: ${errors.join(' | ')}`);
expect(httpFailures.length === 0, `failed requests: ${httpFailures.join(', ')}`);

if (failures.length) { console.error('E2E FAILED:\n  ' + failures.join('\n  ')); cleanup(1); }
console.log(`E2E OK: ${layers} layers, summary, pin, pin filter (${before} -> ${after}), insights, RTL, no console errors`);
cleanup(0);
