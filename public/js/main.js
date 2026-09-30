import { codeColors, codeLabel, fieldLabel, groupLabel, field, getCatalog, loadCatalog, NO_DATA_COLOR, propertyLabel, vocabOf } from './catalog.js';
import { clear, el } from './dom.js';
import { formatNumber, getLang, label, setLang, t } from './i18n.js';
import { ClusterDonuts } from './clusters.js';
import { highlight, renderer, setLayerVisible } from './layers.js';
import { closePanel, initPanel, showDataset, showFeature, showInsights, showList, showPin, showSummary } from './panel.js';

const LEBANON = [[35.1, 33.05], [36.62, 34.69]];
const BASEMAPS = {
	light: { label: { en: 'Light grey', ar: 'رمادي فاتح' }, tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'],
		labels: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}'],
		attribution: 'Basemap © Esri, HERE, Garmin, © OpenStreetMap contributors', maxzoom: 16 },
	osm: { label: { en: 'Streets', ar: 'شوارع' }, tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
		attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' },
	esri: { label: { en: 'Satellite', ar: 'صورة فضائية' }, tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
		attribution: 'Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User Community' },
};

const state = { layers: [], data: {}, index: {}, ui: {}, donuts: {}, basemap: 'light' };
let map;

function setStatus(text) { document.getElementById('status').textContent = text || ''; }

function initMap() {
	const sources = {};
	const layers = [];
	for (const [id, b] of Object.entries(BASEMAPS)) {
		sources[`basemap-${id}`] = { type: 'raster', tiles: b.tiles, tileSize: 256, attribution: b.attribution, maxzoom: b.maxzoom || 19 };
		layers.push({ id: `basemap-${id}`, type: 'raster', source: `basemap-${id}`,
			layout: { visibility: id === state.basemap ? 'visible' : 'none' } });
	}
	map = new maplibregl.Map({
		container: 'map',
		style: { version: 8, glyphs: 'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf', sources, layers },
		bounds: LEBANON,
		fitBoundsOptions: { padding: 20 },
		maxZoom: 16,
		attributionControl: { compact: true },
	});
	map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
	map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');
	return new Promise(resolve => map.on('load', resolve));
}

function buildBasemaps() {
	const box = clear(document.getElementById('basemaps'));
	for (const [id, b] of Object.entries(BASEMAPS)) {
		box.append(el('label', { class: 'radio' },
			el('input', { type: 'radio', name: 'basemap', value: id, checked: id === state.basemap,
				onchange: () => {
					state.basemap = id;
					for (const [other, spec] of Object.entries(BASEMAPS)) {
						map.setLayoutProperty(`basemap-${other}`, 'visibility', other === id ? 'visible' : 'none');
						if (spec.labels) map.setLayoutProperty(`basemap-${other}-labels`, 'visibility', other === id ? 'visible' : 'none');
					}
				} }),
			el('span', { text: label(b.label) })));
	}
}

async function loadLayerData(layer) {
	const res = await fetch(layer.file);
	if (!res.ok) throw new Error(`${layer.file}: HTTP ${res.status}`);
	const fc = await res.json();
	state.index[layer.id] = new Map();
	for (const f of fc.features) {
		f.properties.fid = f.id;  // MapLibre drops string ids; keep them as a property
		state.index[layer.id].set(f.id, f);
	}
	state.data[layer.id] = fc;
	return fc;
}

// ── indicator (shared by every layer that colours by an answer) ──────────

function indicatorControls(layer) {
	const box = [];
	const owner = [...state.layers].reverse().find(l => l.indicators && state.ui[l.id].visible);
	if (owner && owner.id !== layer.id) {
		return [el('p', { class: 'small muted', text: `${t('indicator')}: ${fieldLabel(state.indicator)}` })];
	}
	const select = el('select', { 'aria-label': t('indicator'), onchange: (e) => setIndicator(e.target.value) });
	const byGroup = new Map();
	for (const code of layer.indicators) {
		const g = field(code).group;
		if (!byGroup.has(g)) byGroup.set(g, el('optgroup', { label: groupLabel(g) }));
		byGroup.get(g).append(el('option', { value: code, selected: code === state.indicator, text: fieldLabel(code) }));
	}
	select.append(...byGroup.values());
	box.push(el('label', { class: 'field' }, el('span', { class: 'small muted', text: t('indicator') }), select));
	box.push(legendBlock());
	return box;
}

function legendBlock() {
	const legend = el('ul', { class: 'legend', 'aria-label': t('legend') });
	const dist = pinDistribution(state.indicator);
	const max = dist ? Math.max(1, ...Object.values(dist.counts), dist.none) : 1;
	const entry = (color, text, n) => el('li', { class: dist ? 'with-count' : '' },
		el('span', { class: 'swatch round', style: { background: color } }), el('span', { class: 'legend-text', text }),
		dist ? el('span', { class: 'legend-bar', 'aria-hidden': 'true' },
			el('span', { style: { width: `${(100 * n) / max}%`, background: color } })) : null,
		dist ? el('span', { class: 'legend-count', text: formatNumber(n) }) : null);
	for (const [code, color] of codeColors(state.indicator)) {
		legend.append(entry(color, codeLabel(state.indicator, code), dist ? dist.counts[code] || 0 : 0));
	}
	legend.append(entry(NO_DATA_COLOR, t('noData'), dist ? dist.none : 0));
	const multi = field(state.indicator)?.type === 'multi';
	return el('div', { id: 'indicator-legend' },
		el('p', { class: 'small muted', text: t('colouredBy') + (multi ? ` ${t('firstAnswer')}` : '') }), legend,
		dist ? el('p', { class: 'small muted', text: t('distributionOf', dist.total) }) : null);
}

function updateLegend() {
	const node = document.getElementById('indicator-legend');
	if (node) node.replaceWith(legendBlock());
}

// Distribution of the current indicator among the pins currently shown (respects filters).
function pinDistribution(code) {
	const pins = state.layers.find(l => l.renderer === 'pins' && state.ui[l.id].visible);
	if (!pins) return null;
	const features = state.ui[pins.id].current?.features || state.data[pins.id].features;
	const counts = {};
	let none = 0;
	for (const f of features) {
		const p = f.properties;
		if (p.status?.[code] !== 'reported') { none += 1; continue; }
		const v = p.values[code];
		const first = Array.isArray(v) ? v[0] : v;
		counts[first] = (counts[first] || 0) + 1;
	}
	return { counts, none, total: features.length };
}

function refreshDonuts(layer) {
	const donuts = state.donuts[layer.id];
	if (!donuts) return;
	donuts.configure(codeColors(state.indicator).map(([c]) => c), codeColors(state.indicator).map(([, col]) => col));
	donuts.setEnabled(state.ui[layer.id].visible && !state.ui[layer.id].heatmap);
}

function setIndicator(code) {
	state.indicator = code;
	for (const layer of state.layers) {
		const r = renderer(layer);
		if (!layer.indicators || !r.setIndicator) continue;
		const current = state.ui[layer.id]?.current || state.data[layer.id];
		r.setIndicator(map, layer, code, current, state);
		if (layer.renderer === 'pins') {
			setLayerVisible(map, layer, state.ui[layer.id].visible, state.ui[layer.id]);
			refreshDonuts(layer);
		}
	}
	buildLayerList();
}

// ── filters ──────────────────────────────────────────────────────────────

const has = (value, code) => Array.isArray(value) ? value.includes(code) : value === code;

function pinFilters(layer) {
	const ui = state.ui[layer.id];
	ui.filters = ui.filters || {};
	ui.choices = ui.choices || {};
	const parts = [];
	if (layer.id_search) {
		const input = el('input', { type: 'search', value: ui.search || '', placeholder: t(getCatalog().tier === 'research' ? 'searchIdName' : 'searchId'),
			'aria-label': t('searchId') });
		input.addEventListener('input', () => {
			ui.search = input.value.trim().toLowerCase();
			ui.filters.__search = ui.search ? (f) => {
				const p = f.properties;
				return [p.respondent_id, p.name_latin, p.name_arabic].some(v => v && String(v).toLowerCase().includes(ui.search));
			} : null;
			applyFilters(layer);
		});
		parts.push(el('label', { class: 'field small' }, el('span', { class: 'muted', text: t('searchId') }), input));
	}
	for (const code of layer.filter_fields || []) {
		const vocab = vocabOf(code);
		if (!vocab) continue;
		const select = el('select', { 'aria-label': fieldLabel(code) },
			el('option', { value: '', text: t('all') }),
			vocab.codes.map(c => el('option', { value: c.code, selected: ui.choices[code] === c.code, text: label(c.label) })));
		select.addEventListener('change', () => setChoice(layer, code, select.value));
		parts.push(el('label', { class: 'field small' }, el('span', { class: 'muted', text: fieldLabel(code) }), select));
	}
	const count = el('p', { class: 'small muted', id: `count-${layer.id}` });
	const reset = el('button', { class: 'link-btn small', type: 'button', text: t('clearFilters'),
		onclick: () => { ui.filters = {}; ui.choices = {}; ui.search = ''; applyFilters(layer); buildLayerList(); } });
	return [el('details', { class: 'filters', open: Object.keys(ui.choices).length > 0 || !!ui.search },
		el('summary', { text: t('filterPins') }), ...parts, el('p', {}, reset)), count];
}

function setChoice(layer, code, value) {
	const ui = state.ui[layer.id];
	ui.choices = ui.choices || {};
	ui.filters = ui.filters || {};
	if (value) {
		ui.choices[code] = value;
		ui.filters[code] = (f) => f.properties.status?.[code] === 'reported' && has(f.properties.values[code], value);
	} else {
		delete ui.choices[code];
		delete ui.filters[code];
	}
	applyFilters(layer);
}

function filterControl(layer, filter) {
	const ui = state.ui[layer.id];
	ui.filters = ui.filters || {};
	const values = state.data[layer.id].features.map(f => f.properties[filter.property]).filter(v => v !== null && v !== undefined);
	if (filter.type === 'date_range') {
		const sorted = [...values].sort();
		const from = el('input', { type: 'date', min: sorted[0], max: sorted.at(-1), value: sorted[0] });
		const to = el('input', { type: 'date', min: sorted[0], max: sorted.at(-1), value: sorted.at(-1) });
		const apply = () => {
			ui.filters[filter.property] = (f) => f.properties[filter.property] >= from.value && f.properties[filter.property] <= to.value;
			applyFilters(layer);
		};
		from.addEventListener('change', apply);
		to.addEventListener('change', apply);
		return el('fieldset', { class: 'filter' }, el('legend', { class: 'small', text: propertyLabel(filter.property) }),
			el('label', { class: 'small' }, t('dateFrom'), ' ', from), el('label', { class: 'small' }, t('dateTo'), ' ', to));
	}
	const select = el('select', { 'aria-label': propertyLabel(filter.property) },
		el('option', { value: '', text: t('all') }), [...new Set(values)].sort().map(v => el('option', { value: v, text: v })));
	select.addEventListener('change', () => {
		ui.filters[filter.property] = select.value ? (f) => f.properties[filter.property] === select.value : null;
		applyFilters(layer);
	});
	return el('label', { class: 'field small' }, el('span', { class: 'muted', text: propertyLabel(filter.property) }), select);
}

function applyFilters(layer) {
	const preds = Object.values(state.ui[layer.id].filters || {}).filter(Boolean);
	const all = state.data[layer.id].features;
	const features = preds.length ? all.filter(f => preds.every(fn => fn(f))) : all;
	const current = { type: 'FeatureCollection', features };
	map.getSource(layer.id).setData(current);
	state.ui[layer.id].shown = features.length;
	state.ui[layer.id].current = current;
	if (state.donuts[layer.id]) state.donuts[layer.id].clear();
	if (layer.indicators) updateLegend();
	const count = document.getElementById(`count-${layer.id}`);
	const text = t('showing', features.length, all.length);
	if (count) count.textContent = text;
	setStatus(text);
	return features.length;
}

// ── layer list ───────────────────────────────────────────────────────────

function layerControls(layer) {
	const ui = state.ui[layer.id];
	const box = el('div', { class: 'layer-controls' });
	if (layer.indicators) box.append(...indicatorControls(layer));
	else {
		const swatch = layer.renderer === 'polygons'
			? { background: `${layer.color}22`, border: `3px solid ${layer.color}`, outline: '2px solid #fff', outlineOffset: '-5px' }
			: { background: layer.color };
		box.append(el('ul', { class: 'legend' }, el('li', {},
			el('span', { class: `swatch ${layer.renderer === 'polygons' ? '' : 'round'}`, style: swatch }), label(layer.title))));
	}
	if (layer.renderer === 'pins') box.append(el('p', { class: 'small muted', text: t('pinsApproximate') }), ...pinFilters(layer));
	if (layer.heatmap) {
		box.append(el('label', { class: 'check small' },
			el('input', { type: 'checkbox', checked: ui.heatmap, onchange: (e) => { ui.heatmap = e.target.checked; setLayerVisible(map, layer, ui.visible, ui); } }),
			t('heatmap')));
	}
	for (const filter of layer.filters || []) box.append(filterControl(layer, filter));
	return box;
}

function buildLayerList() {
	const list = clear(document.getElementById('layer-list'));
	for (const layer of [...state.layers].reverse()) {
		const ui = state.ui[layer.id];
		const controls = ui.visible ? layerControls(layer) : null;
		list.append(el('div', { class: 'layer' + (ui.visible ? ' on' : '') },
			el('div', { class: 'layer-head' },
				el('label', { class: 'check' },
					el('input', { type: 'checkbox', checked: ui.visible, onchange: (e) => {
						ui.visible = e.target.checked; setLayerVisible(map, layer, ui.visible, ui);
						if (state.donuts[layer.id]) state.donuts[layer.id].setEnabled(ui.visible && !ui.heatmap);
						buildLayerList();
					} }),
					el('span', { text: label(layer.title) })),
				el('button', { class: 'icon-btn small', type: 'button', title: t('about'), 'aria-label': `${t('about')}: ${label(layer.title)}`,
					onclick: () => showDataset(layer), text: 'ⓘ' }),
				['survey_summary', 'polygons', 'pins'].includes(layer.renderer)
					? el('button', { class: 'icon-btn small', type: 'button', title: t('places'), 'aria-label': `${t('places')}: ${label(layer.title)}`,
						onclick: () => showList(layer, state.data[layer.id].features, selectFeature), text: '☰' })
					: null),
			controls));
		if (layer.renderer === 'pins' && ui.visible) {
			const n = ui.shown ?? state.data[layer.id].features.length;
			const count = document.getElementById(`count-${layer.id}`);
			if (count) count.textContent = t('showing', n, state.data[layer.id].features.length);
		}
	}
}

function selectFeature(layer, feature) {
	highlight(map, state.layers, layer.id, feature.id);
	if (layer.renderer === 'survey_summary') showSummary(layer, feature);
	else if (layer.renderer === 'pins') showPin(layer, feature);
	else showFeature(layer, feature);
	if (feature.geometry && feature.geometry.type === 'Point') {
		map.easeTo({ center: feature.geometry.coordinates, zoom: Math.max(map.getZoom(), 12) });
	} else if (feature.geometry) {
		const b = new maplibregl.LngLatBounds();
		const walk = (c) => (typeof c[0] === 'number' ? b.extend(c) : c.forEach(walk));
		walk(feature.geometry.coordinates);
		map.fitBounds(b, { padding: 60, maxZoom: 12 });
	}
}

function onMapClick(e) {
	// Top-most interactive layer first (catalog order is bottom -> top).
	for (const layer of [...state.layers].reverse()) {
		if (!state.ui[layer.id].visible) continue;
		const ids = renderer(layer).interactive(layer).filter(id => map.getLayer(id));
		const hits = map.queryRenderedFeatures(e.point, { layers: ids });
		if (!hits.length) continue;
		const hit = hits[0];
		if (hit.properties.cluster) {
			map.getSource(layer.id).getClusterExpansionZoom(hit.properties.cluster_id)
				.then(zoom => map.easeTo({ center: hit.geometry.coordinates, zoom: zoom + 0.5 }));
			setStatus(t('clusterHint'));
			return;
		}
		const original = state.index[layer.id].get(hit.properties.fid);
		if (original) selectFeature(layer, original);
		return;
	}
}

// From the Insights panel: colour everything by an indicator and optionally filter pins to one answer.
function focusAnswer(code, value) {
	const pins = state.layers.find(l => l.renderer === 'pins');
	if (pins && !state.ui[pins.id].visible) { state.ui[pins.id].visible = true; setLayerVisible(map, pins, true, state.ui[pins.id]); }
	if (state.layers.some(l => l.indicators?.includes(code))) setIndicator(code);
	if (pins && value !== undefined) {
		setChoice(pins, code, value);
		buildLayerList();
		map.fitBounds(LEBANON, { padding: 20 });
	}
}

async function start() {
	setLang(getLang());
	document.getElementById('toggle-lang').addEventListener('click', () => {
		setLang(getLang() === 'ar' ? 'en' : 'ar');
		buildLayerList();
		buildBasemaps();
		closePanel();
	});
	const panel = document.getElementById('panel');
	const toggle = document.getElementById('toggle-panel');
	toggle.addEventListener('click', () => {
		const open = panel.classList.toggle('collapsed') === false;
		toggle.setAttribute('aria-expanded', String(open));
	});
	if (window.matchMedia('(max-width: 720px)').matches) { panel.classList.add('collapsed'); toggle.setAttribute('aria-expanded', 'false'); }
	initPanel(() => highlight(map, state.layers, null, null));

	setStatus(t('loading'));
	try {
		const [catalog] = await Promise.all([loadCatalog(), initMap()]);
		if (catalog.tier === 'research') {
			const banner = document.getElementById('tier-banner');
			banner.hidden = false;
			banner.textContent = t('researchBanner');
		}
		const insightsBtn = document.getElementById('open-insights');
		if (catalog.insights) {
			insightsBtn.hidden = false;
			insightsBtn.addEventListener('click', () => showInsights(catalog.insights, focusAnswer));
		}
		state.layers = catalog.layers;
		state.indicator = catalog.layers.find(l => l.default_indicator && catalog.fields[l.default_indicator])?.default_indicator
			|| catalog.layers.find(l => l.indicators)?.indicators[0];
		await Promise.all(state.layers.map(loadLayerData));
		for (const layer of state.layers) {
			state.ui[layer.id] = { visible: !!layer.visible, heatmap: false };
			renderer(layer).add(map, layer, state.data[layer.id], state);
			setLayerVisible(map, layer, state.ui[layer.id].visible, state.ui[layer.id]);
			for (const id of renderer(layer).interactive(layer)) {
				map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer'; });
				map.on('mouseleave', id, () => { map.getCanvas().style.cursor = ''; });
			}
		}
		// Basemap place names above areas but below point layers, so pins stay clickable and visible.
		const firstPoints = state.layers.find(l => ['points', 'pins'].includes(l.renderer));
		const before = firstPoints ? renderer(firstPoints).layerIds(firstPoints).find(id => map.getLayer(id)) : undefined;
		for (const [id, b] of Object.entries(BASEMAPS)) {
			if (!b.labels) continue;
			map.addSource(`basemap-${id}-labels`, { type: 'raster', tiles: b.labels, tileSize: 256, maxzoom: b.maxzoom || 19 });
			map.addLayer({ id: `basemap-${id}-labels`, type: 'raster', source: `basemap-${id}-labels`,
				layout: { visibility: id === state.basemap ? 'visible' : 'none' } }, before);
		}
		for (const layer of state.layers.filter(l => l.renderer === 'pins' && l.cluster)) {
			state.donuts[layer.id] = new ClusterDonuts(map, layer.id);
			refreshDonuts(layer);
		}
		let pending = false;
		map.on('render', () => {
			if (pending) return;
			pending = true;
			requestAnimationFrame(() => { pending = false; for (const d of Object.values(state.donuts)) d.update(); });
		});
		map.on('click', onMapClick);
		// Open framed on the survey respondents (the map's main subject), not on all of Lebanon.
		const pins = state.layers.find(l => l.renderer === 'pins');
		if (pins && state.data[pins.id].features.length) {
			const b = new maplibregl.LngLatBounds();
			for (const f of state.data[pins.id].features) b.extend(f.geometry.coordinates);
			map.fitBounds(b, { padding: 60, maxZoom: 11, duration: 0 });
		}
		buildBasemaps();
		buildLayerList();
		setStatus('');
	} catch (err) {
		console.error(err);
		setStatus(t('loadFailed'));
	}
}

start();
