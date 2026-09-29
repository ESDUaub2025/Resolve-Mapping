// Generic renderers keyed by the catalog's `renderer` value. No dataset-specific code here.
import { codeColors, NO_DATA_COLOR } from './catalog.js';

const FONT = ['Noto Sans Regular'];

function matchColor(property, fieldCode) {
	const pairs = codeColors(fieldCode).flat();
	if (!pairs.length) return NO_DATA_COLOR;
	return ['match', ['coalesce', ['get', property], '__none__'], ...pairs, NO_DATA_COLOR];
}

function setVisibility(map, ids, visible) {
	for (const id of ids) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none');
}

const surveySummary = {
	layerIds: (l) => [`${l.id}-fill`, `${l.id}-line`, `${l.id}-selected`],
	interactive: (l) => [`${l.id}-fill`],
	add(map, l, data, state) {
		map.addSource(l.id, { type: 'geojson', data });
		map.addLayer({ id: `${l.id}-fill`, type: 'fill', source: l.id,
			paint: { 'fill-color': matchColor(`mode__${state.indicator}`, state.indicator), 'fill-opacity': 0.55 } });
		map.addLayer({ id: `${l.id}-line`, type: 'line', source: l.id,
			paint: { 'line-color': '#ffffff', 'line-width': 1.2 } });
		map.addLayer({ id: `${l.id}-selected`, type: 'line', source: l.id, filter: ['==', ['get', 'fid'], ''],
			paint: { 'line-color': '#111111', 'line-width': 3 } });
	},
	setIndicator(map, l, indicator) {
		map.setPaintProperty(`${l.id}-fill`, 'fill-color', matchColor(`mode__${indicator}`, indicator));
	},
};

// Context polygons with a strong, readable border: white casing under a solid coloured line,
// a light fill, and name labels from zoom 8.
const polygons = {
	layerIds: (l) => [`${l.id}-fill`, `${l.id}-casing`, `${l.id}-line`, `${l.id}-label`, `${l.id}-selected`],
	interactive: (l) => [`${l.id}-fill`],
	add(map, l, data) {
		const strong = l.outline === 'strong';
		map.addSource(l.id, { type: 'geojson', data });
		map.addLayer({ id: `${l.id}-fill`, type: 'fill', source: l.id, paint: { 'fill-color': l.color, 'fill-opacity': strong ? 0.1 : 0.06 } });
		map.addLayer({ id: `${l.id}-casing`, type: 'line', source: l.id,
			paint: { 'line-color': '#ffffff', 'line-width': strong ? ['interpolate', ['linear'], ['zoom'], 7, 4, 12, 7] : 0 } });
		map.addLayer({ id: `${l.id}-line`, type: 'line', source: l.id,
			paint: { 'line-color': l.color, 'line-width': strong ? ['interpolate', ['linear'], ['zoom'], 7, 2, 12, 3.5] : 1.8,
				...(l.dash ? { 'line-dasharray': [3, 2] } : {}) } });
		if (l.label_property) {
			map.addLayer({ id: `${l.id}-label`, type: 'symbol', source: l.id, minzoom: 8,
				layout: { 'text-field': ['get', l.label_property], 'text-font': FONT, 'text-size': 12, 'text-max-width': 10 },
				paint: { 'text-color': l.color, 'text-halo-color': '#ffffff', 'text-halo-width': 1.6 } });
		}
		map.addLayer({ id: `${l.id}-selected`, type: 'line', source: l.id, filter: ['==', ['get', 'fid'], ''],
			paint: { 'line-color': '#111111', 'line-width': 4 } });
	},
};

function clusteredPoints(radius, colorBy) {
	return {
		layerIds: (l) => [`${l.id}-clusters`, `${l.id}-count`, `${l.id}-points`, `${l.id}-selected`].concat(l.heatmap ? [`${l.id}-heat`] : []),
		interactive: (l) => [`${l.id}-clusters`, `${l.id}-points`],
		add(map, l, data, state) {
			map.addSource(l.id, { type: 'geojson', data, cluster: !!l.cluster, clusterRadius: colorBy ? 25 : 40, clusterMaxZoom: colorBy ? 10 : 13 });
			if (l.heatmap) {
				map.addLayer({ id: `${l.id}-heat`, type: 'heatmap', source: l.id, layout: { visibility: 'none' },
					paint: {
						'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 7, 12, 12, 28],
						'heatmap-weight': ['case', ['has', 'point_count'], ['get', 'point_count'], 1],
						'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'],
							0, 'rgba(255,255,178,0)', 0.2, '#fecc5c', 0.5, '#fd8d3c', 0.8, '#f03b20', 1, '#bd0026'],
					} });
			}
			map.addLayer({ id: `${l.id}-clusters`, type: 'circle', source: l.id, filter: ['has', 'point_count'],
				paint: {
					'circle-color': l.color, 'circle-opacity': 0.8, 'circle-stroke-color': '#fff', 'circle-stroke-width': 2,
					'circle-radius': ['step', ['get', 'point_count'], 12, 10, 16, 50, 21, 200, 27],
				} });
			map.addLayer({ id: `${l.id}-count`, type: 'symbol', source: l.id, filter: ['has', 'point_count'],
				layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': FONT, 'text-size': 12 },
				paint: { 'text-color': '#ffffff' } });
			map.addLayer({ id: `${l.id}-points`, type: 'circle', source: l.id, filter: ['!', ['has', 'point_count']],
				paint: {
					'circle-color': colorBy ? matchColor(`c__${state.indicator}`, state.indicator) : l.color,
					'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, radius - 1, 14, radius + 2],
					'circle-stroke-color': colorBy ? '#222' : '#fff', 'circle-stroke-width': colorBy ? 1.3 : 1.2,
				} });
			map.addLayer({ id: `${l.id}-selected`, type: 'circle', source: l.id, filter: ['==', ['get', 'fid'], ''],
				paint: { 'circle-radius': radius + 5, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#111', 'circle-stroke-width': 3 } });
		},
		setIndicator: colorBy ? (map, l, indicator) => {
			map.setPaintProperty(`${l.id}-points`, 'circle-color', matchColor(`c__${indicator}`, indicator));
		} : undefined,
		setHeatmap(map, l, on) {
			setVisibility(map, [`${l.id}-heat`], on);
			setVisibility(map, [`${l.id}-clusters`, `${l.id}-count`, `${l.id}-points`], !on);
		},
	};
}

export const RENDERERS = {
	survey_summary: surveySummary,
	polygons,
	points: clusteredPoints(5, false),
	pins: clusteredPoints(6, true),
};

export function renderer(layer) {
	const r = RENDERERS[layer.renderer];
	if (!r) throw new Error(`Unknown renderer ${layer.renderer} for layer ${layer.id}`);
	return r;
}

export function setLayerVisible(map, layer, visible, state) {
	const r = renderer(layer);
	setVisibility(map, r.layerIds(layer), visible);
	if (visible && r.setHeatmap && layer.heatmap) r.setHeatmap(map, layer, !!state.heatmap);
}

export function highlight(map, layers, layerId, featureId) {
	for (const l of layers) {
		const id = `${l.id}-selected`;
		if (map.getLayer(id)) map.setFilter(id, ['==', ['get', 'fid'], l.id === layerId ? featureId : '']);
	}
}

// Pins that share an anchor (a village or district centre) are laid out in a sunflower pattern
// around it so each one can be clicked. Only the displayed position moves; the data keeps the
// honest anchor, and the popup says the position is approximate.
export function spreadPins(features) {
	const groups = new Map();
	for (const f of features) {
		const key = f.geometry.coordinates.join(',');
		if (!groups.has(key)) groups.set(key, []);
		groups.get(key).push(f);
	}
	const golden = Math.PI * (3 - Math.sqrt(5));
	for (const group of groups.values()) {
		const [lon, lat] = group[0].geometry.coordinates;
		const step = (group[0].properties.spread_m || 150) / Math.sqrt(Math.max(group.length, 1)) * 1.4;
		group.forEach((f, i) => {
			if (i === 0 && group.length === 1) return;
			const r = step * Math.sqrt(i + 0.5);
			const a = i * golden;
			const dLat = (r * Math.sin(a)) / 111320;
			const dLon = (r * Math.cos(a)) / (111320 * Math.cos((lat * Math.PI) / 180));
			f.properties.anchor = [lon, lat];
			f.geometry = { type: 'Point', coordinates: [lon + dLon, lat + dLat] };
		});
	}
	return features;
}
