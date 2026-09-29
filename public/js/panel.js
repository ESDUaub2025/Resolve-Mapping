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

// Research tier only: a single respondent's standardized record, including identity.
export function showRespondent(layer, feature) {
	const p = typeof feature.properties.values === 'string'
		? { ...feature.properties, values: JSON.parse(feature.properties.values), status: JSON.parse(feature.properties.status) }
		: feature.properties;
	const identity = el('dl', { class: 'props identity' },
		...(layer.identity_properties || []).map(key => el('div', { class: 'row' },
			el('dt', { text: propertyLabel(key) === key ? fieldLabel(key) : propertyLabel(key) }),
			el('dd', { text: p[key] ?? statusLabel('not_provided') }))));
	const location = el('dl', { class: 'props' },
		el('div', { class: 'row' }, el('dt', { text: t('location') }), el('dd', { text: label({ en: p.locality_name_en, ar: p.locality_name_ar }) || '—' })),
		el('div', { class: 'row' }, el('dt', { text: t('precision') }),
			el('dd', { text: `${precisionLabel(p.spatial_precision)}${p.uncertainty_m ? ` (±${formatNumber(p.uncertainty_m)} m)` : ''}` })),
		el('div', { class: 'row' }, el('dt', { text: t('source') }), el('dd', { text: `${p.instrument} · row ${p.source?.row ?? JSON.parse(p.source || '{}').row}` })));
	const byGroup = new Map();
	for (const [code, def] of Object.entries(getCatalog().fields)) {
		if (def.privacy === 'identity') continue;
		const status = p.status[code];
		const value = p.values[code];
		let text;
		if (status !== 'reported') text = statusLabel(status);
		else if (def.vocab) text = (Array.isArray(value) ? value : [value]).map(c => codeLabel(code, c)).join(', ');
		else text = String(value);
		if (!byGroup.has(def.group)) byGroup.set(def.group, []);
		byGroup.get(def.group).push(el('div', { class: 'row' }, el('dt', { text: label(def.label) }),
			el('dd', { class: status === 'reported' ? '' : 'muted', text })));
	}
	const groups = [...byGroup].map(([g, rows]) => el('details', { class: 'group', open: true },
		el('summary', { text: groupLabel(g) }), el('dl', { class: 'props' }, rows)));
	open(`${t('identity')}: ${p.respondent_id}`, identity, location, groups);
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
	const nameOf = (p) => p.entity_type === 'survey_respondent'
		? `${p.respondent_id} — ${label({ en: p.name_latin || p.name_arabic, ar: p.name_arabic || p.name_latin })} (${label({ en: p.locality_name_en, ar: p.locality_name_ar })})`
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
