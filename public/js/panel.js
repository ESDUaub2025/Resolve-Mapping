// Details panel: survey summaries, feature properties, respondent records and dataset cards.
import { codeColors, codeLabel, field, fieldLabel, getCatalog, groupLabel, precisionLabel, propertyLabel, statusLabel } from './catalog.js';
import { clear, el } from './dom.js';
import { formatNumber, label, t } from './i18n.js';

const panel = () => document.getElementById('details');
const body = () => document.getElementById('details-body');
let onClose = null;

export function initPanel(closeHandler) {
	onClose = closeHandler;
	document.getElementById('details-close').addEventListener('click', closePanel);
	document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !panel().hidden) closePanel(); });
}

export function closePanel() {
	panel().hidden = true;
	if (onClose) onClose();
}

function open(title, ...content) {
	document.getElementById('details-title').textContent = title;
	clear(body()).append(...content.flat().filter(Boolean));
	panel().hidden = false;
	body().scrollTop = 0;
}

function pct(n, d) { return d ? Math.round((100 * n) / d) : 0; }

// One indicator: bars per answer code, suppression notes, and counts of non-answers by status.
function indicatorBlock(code, summary, k) {
	const block = el('div', { class: 'indicator' }, el('h4', { text: fieldLabel(code) }));
	const colors = Object.fromEntries(codeColors(code));
	if (summary.suppressed === 'fewer_than_k_answers' || !summary.counts) {
		block.append(el('p', { class: 'muted small', text: summary.n_answered ? t('suppressedFewer', k) : t('noData') }));
	} else {
		const list = el('ul', { class: 'bars', role: 'list' });
		for (const [value, count] of Object.entries(summary.counts)) {
			if (count === 0) continue;
			const hidden = count === null;
			const width = hidden ? 0 : pct(count, summary.n_answered);
			list.append(el('li', {},
				el('span', { class: 'bar-label', text: codeLabel(code, value) }),
				el('span', { class: 'bar-track', 'aria-hidden': 'true' },
					el('span', { class: 'bar-fill', style: { width: `${width}%`, background: colors[value] || '#888' } })),
				el('span', { class: 'bar-value', text: hidden ? `< 3 (${t('hiddenCount')})` : `${formatNumber(count)} (${width}%)` })));
		}
		block.append(list, el('p', { class: 'muted small', text: `${formatNumber(summary.n_answered)} ${t('answered')}` }));
		if (field(code)?.type === 'multi') block.lastChild.textContent += ` · ${t('multiNote')}`;
		if (summary.suppressed === 'small_cells') block.append(el('p', { class: 'muted small', text: t('suppressedCells') }));
	}
	const nonAnswers = Object.entries(summary.status_counts || {}).filter(([, n]) => n > 0);
	if (nonAnswers.length) {
		block.append(el('p', { class: 'status-line small' },
			`${t('statusOf')}: `, nonAnswers.map(([s, n]) => `${statusLabel(s)} ${formatNumber(n)}`).join(' · ')));
	}
	return block;
}

function groupedIndicators(codes, indicators, k) {
	const byGroup = new Map();
	for (const code of codes) {
		if (!indicators[code]) continue;
		const g = field(code).group;
		if (!byGroup.has(g)) byGroup.set(g, []);
		byGroup.get(g).push(indicatorBlock(code, indicators[code], k));
	}
	return [...byGroup].map(([g, blocks]) => el('details', { class: 'group', open: true },
		el('summary', { text: groupLabel(g) }), ...blocks));
}

export function showSummary(layer, feature) {
	const p = feature.properties;
	const k = getCatalog().k_min_respondents;
	const isDistrict = p.entity_type === 'district_survey_summary';
	const name = label({ en: p.name_en, ar: p.name_ar });
	const head = [
		el('p', { class: 'lead' }, `${formatNumber(p.n_respondents)} ${t('respondents')}`,
			p.district_en ? ` · ${label({ en: p.district_en, ar: p.district_ar })}` : ''),
		el('p', { class: 'precision small' }, `${t('precision')}: ${precisionLabel(p.spatial_precision)}`),
		el('p', { class: 'muted small', text: (p.instruments || []).map(i => label(getCatalog().instruments[i]?.title)).join(' · ') }),
	];
	const ctx = Object.entries(p.context || {});
	if (ctx.length) {
		head.push(el('details', { class: 'group', open: true }, el('summary', { text: t('context') }),
			el('dl', { class: 'props' }, ctx.map(([key, value]) => el('div', { class: 'row' },
				el('dt', { text: propertyLabel(key) }), el('dd', { text: formatNumber(value) }))))));
	}
	const sections = [];
	if (isDistrict) {
		sections.push(el('h3', { text: t('sensitiveNote') }));
		sections.push(...groupedIndicators(layer.sensitive_indicators || [], p.indicators || {}, k));
		sections.push(el('h3', { text: t('otherVillages') }),
			el('p', { class: 'muted small', text: t('otherVillagesNote', p.n_remainder, p.remainder_villages) }));
		sections.push(...groupedIndicators(layer.indicators, p.remainder_indicators || {}, k));
	} else {
		sections.push(...groupedIndicators(layer.indicators, p.indicators || {}, k));
	}
	open(name, head, sections, datasetLink(layer));
}

function valueText(key, value) {
	if (value === null || value === undefined || value === '') return null;
	if (key === 'spatial_precision') return precisionLabel(value);
	return typeof value === 'number' ? formatNumber(value) : String(value);
}

export function showFeature(layer, feature) {
	const p = feature.properties;
	const rows = (layer.popup_properties || []).map(key => {
		const v = valueText(key, p[key]);
		return el('div', { class: 'row' }, el('dt', { text: propertyLabel(key) }),
			el('dd', { class: v === null ? 'muted' : '', text: v === null ? statusLabel('not_provided') : v }));
	});
	rows.push(el('div', { class: 'row' }, el('dt', { text: t('precision') }), el('dd', { text: precisionLabel(p.spatial_precision) })));
	open(label(layer.title), el('dl', { class: 'props' }, rows), datasetLink(layer));
}

function answerText(code, def, status, value) {
	if (status !== 'reported') return statusLabel(status);
	if (def.vocab) return (Array.isArray(value) ? value : [value]).map(c => codeLabel(code, c)).join(', ');
	return String(value);
}

// One respondent's pin. Public tier: ID and farming-practice answers only, shown at an approximate
// position. Research tier (local): identity and every standardized answer.
export function showPin(layer, feature) {
	const p = feature.properties;
	const blocks = [];
	if (layer.identity_properties) {
		blocks.push(el('dl', { class: 'props identity' },
			...layer.identity_properties.map(key => el('div', { class: 'row' },
				el('dt', { text: propertyLabel(key) === key ? fieldLabel(key) : propertyLabel(key) }),
				el('dd', { text: p[key] ?? statusLabel('not_provided') })))));
	}
	const area = label({ en: p.area_name_en, ar: p.area_name_ar }) || '—';
	blocks.push(el('p', { class: 'lead', text: area }),
		el('p', { class: 'precision small', text: `${t('precision')}: ${precisionLabel(p.spatial_precision)}`
			+ (p.uncertainty_m ? ` (±${formatNumber(p.uncertainty_m)} m)` : '') }),
		el('p', { class: 'muted small', text: p.spatial_precision === 'district' ? t('pinDistrictNote') : t('pinSpreadNote') }),
		el('p', { class: 'muted small', text: label(getCatalog().instruments[p.instrument]?.title) }));
	const byGroup = new Map();
	for (const [code, def] of Object.entries(getCatalog().fields)) {
		if (def.privacy === 'identity' || !(code in (p.status || {}))) continue;
		if (!byGroup.has(def.group)) byGroup.set(def.group, []);
		const status = p.status[code];
		byGroup.get(def.group).push(el('div', { class: 'row' }, el('dt', { text: label(def.label) }),
			el('dd', { class: status === 'reported' ? '' : 'muted', text: answerText(code, def, status, p.values[code]) })));
	}
	const order = Object.keys(getCatalog().groups);
	const groups = [...byGroup].sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]))
		.map(([g, rows]) => el('details', { class: 'group', open: g === 'analysis' || g === 'water' },
			el('summary', { text: groupLabel(g) }), el('dl', { class: 'props' }, rows)));
	open(`${t('idLabel')} ${p.respondent_id}`, blocks, groups, datasetLink(layer));
}

// ── Insights: analysis results (aggregates only) ─────────────────────────

function share(x) { return `${Math.round(x * 100)}%`; }

function colorOf(code, value) {
	return Object.fromEntries(codeColors(code))[value] || '#888';
}

function verdict(model) {
	const lo = model.auc_ci[0];
	if (!model.predictive) return t('modelNone');
	return lo >= 0.65 ? t('modelStrong') : lo >= 0.55 ? t('modelModerate') : t('modelWeak');
}

// Odds ratio and its 95% interval on a log scale from 1/10 to 10 (1 = no difference).
function orBar(or, ci) {
	const pos = (v) => Math.min(100, Math.max(0, (Math.log10(v) + 1) * 50));
	return el('span', { class: 'or-track', 'aria-hidden': 'true' },
		el('span', { class: 'or-one' }),
		el('span', { class: 'or-ci', style: { insetInlineStart: `${pos(ci[0])}%`, width: `${pos(ci[1]) - pos(ci[0])}%` } }),
		el('span', { class: 'or-dot', style: { insetInlineStart: `${pos(or)}%` } }));
}

export function showInsights(insights, focus) {
	const catalog = getCatalog();
	const regionName = (k) => label(catalog.instruments[k]?.title);
	const parts = [el('p', { class: 'small', text: t('insightsIntro') })];
	const typo = insights.typology;
	parts.push(el('h3', { text: t('typologyTitle') }));
	if (!typo.published) {
		parts.push(el('p', { class: 'muted small', text: t('typologyNotPublished', typo.stability_ari) }));
	} else {
		parts.push(el('p', { class: 'small muted', text: t('typologyMethod', typo.n, typo.k, typo.stability_ari) }),
			el('p', {}, el('button', { class: 'link-btn', type: 'button', text: t('colourByType'), onclick: () => focus('farmer_type') })));
		for (const type of typo.types) {
			const regions = Object.entries(type.regions).map(([k, n]) => `${regionName(k)}: ${formatNumber(n)}`).join(' · ');
			parts.push(el('div', { class: 'insight-card' },
				el('h4', {}, el('span', { class: 'swatch round', style: { background: colorOf('farmer_type', type.code) } }), ' ', label(type.name)),
				el('p', { class: 'small muted', text: `${formatNumber(type.size)} ${t('respondents')} · ${regions}` }),
				el('ul', { class: 'traits' }, type.traits.map(tr => el('li', {},
					el('span', { text: label(tr.label) }),
					el('span', { class: 'muted', text: ` — ${share(tr.share_in_type)} ${t('vsAll')} ${share(tr.share_overall)}` })))),
				el('button', { class: 'link-btn small', type: 'button', text: t('showTypePins'), onclick: () => focus('farmer_type', type.code) })));
		}
	}
	for (const d of Object.values(insights.drivers)) {
		const regions = Object.entries(d.prevalence_by_region).map(([k, v]) => `${regionName(k)} ${share(v)}`).join(' · ');
		parts.push(el('h3', { text: label(d.label) }),
			el('p', { class: 'small', text: `${label(d.definition)}. ${t('prevalence')}: ${share(d.prevalence)} (${regions}); n = ${formatNumber(d.n)}.` }),
			el('p', { class: 'small' }, el('strong', { text: verdict(d.model) }), ' ',
				t('modelDetail', d.model.auc, d.model.auc_ci, d.model.baseline_auc)));
		if (d.findings.length) {
			parts.push(el('ul', { class: 'findings' }, d.findings.map(f => el('li', {},
				el('button', { class: 'link-btn', type: 'button', text: label(f.label), onclick: () => focus(f.field, f.code) }),
				el('div', { class: 'small', text: t('findingRates', share(f.rate_with), f.n_with, share(f.rate_without), f.n_without) }),
				el('div', { class: 'or-row small' }, orBar(f.or, f.ci), el('span', { text: t('findingOr', f.or, f.ci, f.q < 0.001 ? '< 0.001' : `= ${f.q}`) }))))));
		} else {
			parts.push(el('p', { class: 'muted small', text: t('noFindings', d.tests_run) }));
		}
		parts.push(el('p', { class: 'muted small', text: `${t('caveatLabel')}: ${label(d.caveat)}` }));
	}
	parts.push(el('h3', { text: t('howToRead') }), el('ul', { class: 'caveats' },
		['readNotCausal', 'readSample', 'readOr', 'readValidation'].map(key => el('li', { text: t(key) }))));
	open(t('insightsTitle'), parts);
}

function datasetLink(layer) {
	return el('p', {}, el('button', { class: 'link-btn', type: 'button', onclick: () => showDataset(layer), text: t('about') }));
}

export function showDataset(layer) {
	const card = getCatalog().datasets[layer.dataset];
	if (!card) return;
	const row = (key, value) => value ? el('div', { class: 'row' }, el('dt', { text: t(key) }), el('dd', { text: label(value) })) : null;
	const caveats = (card.caveats || []).length
		? [el('h3', { text: t('caveats') }), el('ul', { class: 'caveats' }, card.caveats.map(c => el('li', { text: label(c) })))]
		: [];
	open(label(card.title), el('dl', { class: 'props' },
		row('owner', card.owner), row('source', card.source), row('licence', card.licence),
		row('consent', card.consent), row('method', card.method), row('citation', card.citation)), caveats);
}

// Keyboard- and screen-reader-accessible list of a layer's features.
export function showList(layer, features, select) {
	const nameOf = (p) => p.respondent_id
		? [p.respondent_id, p.name_latin || p.name_arabic, `(${label({ en: p.area_name_en, ar: p.area_name_ar })})`]
			.filter(Boolean).join(' ')
		: label({ en: p.name_en ?? p.name, ar: p.name_ar ?? p.name });
	const items = features
		.map(f => ({ f, name: nameOf(f.properties) }))
		.sort((a, b) => a.name.localeCompare(b.name));
	open(`${label(layer.title)} — ${t('places')}`,
		el('ul', { class: 'place-list' }, items.map(({ f, name }) => el('li', {},
			el('button', { class: 'link-btn', type: 'button', onclick: () => select(layer, f), text: name }),
			f.properties.n_respondents ? ` (${formatNumber(f.properties.n_respondents)})` : ''))),
		datasetLink(layer));
}
