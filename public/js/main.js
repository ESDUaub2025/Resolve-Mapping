import { codeColors, codeLabel, fieldLabel, groupLabel, field, loadCatalog, NO_DATA_COLOR, propertyLabel } from './catalog.js';
import { clear, el } from './dom.js';
import { getLang, label, setLang, t } from './i18n.js';
import { highlight, renderer, setLayerVisible } from './layers.js';
import { closePanel, initPanel, showDataset, showFeature, showList, showRespondent, showSummary } from './panel.js';

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

const state = { layers: [], data: {}, index: {}, ui: {}, basemap: 'light' };
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

// Legend + controls for one layer, generated from the catalog.
function layerControls(layer) {
	const ui = state.ui[layer.id];
	const box = el('div', { class: 'layer-controls' });
	const firstSurvey = [...state.layers].reverse().find(l => l.renderer === 'survey_summary' && state.ui[l.id].visible);
	if (layer.renderer === 'survey_summary' && firstSurvey && firstSurvey.id !== layer.id) {
		box.append(el('p', { class: 'small muted', text: `${t('indicator')}: ${fieldLabel(state.indicator)}` }));
	} else if (layer.renderer === 'survey_summary') {
		const select = el('select', { 'aria-label': t('indicator'), onchange: (e) => setIndicator(e.target.value) });
		const byGroup = new Map();
		for (const code of layer.indicators) {
			const g = field(code).group;
			if (!byGroup.has(g)) byGroup.set(g, el('optgroup', { label: groupLabel(g) }));
			byGroup.get(g).append(el('option', { value: code, selected: code === state.indicator, text: fieldLabel(code) }));
		}
		select.append(...byGroup.values());
		box.append(el('label', { class: 'field' }, el('span', { class: 'small muted', text: t('indicator') }), select));
		const legend = el('ul', { class: 'legend', 'aria-label': t('legend') });
		for (const [code, color] of codeColors(state.indicator)) {
			legend.append(el('li', {}, el('span', { class: 'swatch', style: { background: color } }), codeLabel(state.indicator, code)));
		}
		legend.append(el('li', {}, el('span', { class: 'swatch', style: { background: NO_DATA_COLOR } }), t('noData')));
		box.append(el('p', { class: 'small muted', text: t('colouredBy') }), legend);
	} else {
		box.append(el('ul', { class: 'legend' }, el('li', {},
			el('span', { class: `swatch ${layer.renderer === 'polygons' ? '' : 'round'}`,
				style: layer.dash ? { background: 'transparent', border: `2px dashed ${layer.color}` } : { background: layer.color } }),
			label(layer.title))));
	}
	if (layer.heatmap) {
		box.append(el('label', { class: 'check small' },
			el('input', { type: 'checkbox', checked: ui.heatmap, onchange: (e) => { ui.heatmap = e.target.checked; setLayerVisible(map, layer, ui.visible, ui); } }),
			t('heatmap')));
	}
	for (const filter of layer.filters || []) box.append(filterControl(layer, filter));
	return box;
}

function filterControl(layer, filter) {
	const ui = state.ui[layer.id];
	ui.filters = ui.filters || {};
	const values = state.data[layer.id].features.map(f => f.properties[filter.property]).filter(v => v !== null && v !== undefined);
	if (filter.type === 'date_range') {
		const sorted = [...values].sort();
		const from = el('input', { type: 'date', min: sorted[0], max: sorted.at(-1), value: sorted[0] });
		const to = el('input', { type: 'date', min: sorted[0], max: sorted.at(-1), value: sorted.at(-1) });
		const apply = () => { ui.filters[filter.property] = (v) => v >= from.value && v <= to.value; applyFilters(layer); };
		from.addEventListener('change', apply);
		to.addEventListener('change', apply);
		return el('fieldset', { class: 'filter' }, el('legend', { class: 'small', text: propertyLabel(filter.property) }),
			el('label', { class: 'small' }, t('dateFrom'), ' ', from), el('label', { class: 'small' }, t('dateTo'), ' ', to));
	}
	const select = el('select', { 'aria-label': propertyLabel(filter.property) },
		el('option', { value: '', text: t('all') }), [...new Set(values)].sort().map(v => el('option', { value: v, text: v })));
	select.addEventListener('change', () => {
		ui.filters[filter.property] = select.value ? (v) => v === select.value : null;
		applyFilters(layer);
	});
	return el('label', { class: 'field small' }, el('span', { class: 'muted', text: propertyLabel(filter.property) }), select);
}

function applyFilters(layer) {
	const preds = Object.entries(state.ui[layer.id].filters || {}).filter(([, fn]) => fn);
	const fc = state.data[layer.id];
	const features = preds.length ? fc.features.filter(f => preds.every(([prop, fn]) => fn(f.properties[prop]))) : fc.features;
	map.getSource(layer.id).setData({ type: 'FeatureCollection', features });
	setStatus(t('features', features.length));
}

function setIndicator(code) {
	state.indicator = code;
	for (const layer of state.layers.filter(l => l.renderer === 'survey_summary')) renderer(layer).setIndicator(map, layer, code);
	buildLayerList();
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
						ui.visible = e.target.checked; setLayerVisible(map, layer, ui.visible, ui); buildLayerList();
					} }),
					el('span', { text: label(layer.title) })),
				el('button', { class: 'icon-btn small', type: 'button', title: t('about'), 'aria-label': `${t('about')}: ${label(layer.title)}`,
					onclick: () => showDataset(layer), text: 'ⓘ' }),
				['survey_summary', 'polygons', 'respondents'].includes(layer.renderer)
					? el('button', { class: 'icon-btn small', type: 'button', title: t('places'), 'aria-label': `${t('places')}: ${label(layer.title)}`,
						onclick: () => showList(layer, state.data[layer.id].features, selectFeature), text: '☰' })
					: null),
			controls));
	}
}

function selectFeature(layer, feature) {
	highlight(map, state.layers, layer.id, feature.id);
	if (layer.renderer === 'survey_summary') showSummary(layer, feature);
	else if (layer.renderer === 'respondents') showRespondent(layer, feature);
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
				.then(zoom => map.easeTo({ center: hit.geometry.coordinates, zoom }));
			setStatus(t('clusterHint'));
			return;
		}
		const original = state.index[layer.id].get(hit.properties.fid);
		if (original) selectFeature(layer, original);
		return;
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
		state.layers = catalog.layers;
		state.indicator = catalog.layers.find(l => l.default_indicator)?.default_indicator;
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
		// Basemap place names go above the data so they stay readable over filled areas.
		for (const [id, b] of Object.entries(BASEMAPS)) {
			if (!b.labels) continue;
			map.addSource(`basemap-${id}-labels`, { type: 'raster', tiles: b.labels, tileSize: 256, maxzoom: b.maxzoom || 19 });
			map.addLayer({ id: `basemap-${id}-labels`, type: 'raster', source: `basemap-${id}-labels`,
				layout: { visibility: id === state.basemap ? 'visible' : 'none' } });
		}
		map.on('click', onMapClick);
		buildBasemaps();
		buildLayerList();
		setStatus('');
	} catch (err) {
		console.error(err);
		setStatus(t('loadFailed'));
	}
}

start();
