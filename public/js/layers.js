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

// Per-answer counts inside each cluster, for the donut charts (see clusters.js).
function clusterProperties(indicator) {
	const props = {};
	codeColors(indicator).forEach(([code], i) => {
		props[`k${i}`] = ['+', ['case', ['==', ['get', `c__${indicator}`], code], 1, 0]];
	});
	return props;
}

function clusteredPoints(radius, colorBy) {
	const ids = (l) => [`${l.id}-clusters`, `${l.id}-count`, `${l.id}-points`, `${l.id}-selected`].concat(l.heatmap ? [`${l.id}-heat`] : []);
	const r = {
		layerIds: ids,
		interactive: (l) => [`${l.id}-clusters`, `${l.id}-points`],
		add(map, l, data, state) {
			map.addSource(l.id, {
				type: 'geojson', data, cluster: !!l.cluster,
				clusterRadius: colorBy ? 28 : 40, clusterMaxZoom: colorBy ? 12 : 13,
				...(colorBy ? { clusterProperties: clusterProperties(state.indicator) } : {}),
			});
			if (l.heatmap) {
				map.addLayer({ id: `${l.id}-heat`, type: 'heatmap', source: l.id, layout: { visibility: 'none' },
					paint: {
						'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 7, 12, 12, 28],
						'heatmap-weight': ['case', ['has', 'point_count'], ['get', 'point_count'], 1],
						'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'],
							0, 'rgba(255,255,178,0)', 0.2, '#fecc5c', 0.5, '#fd8d3c', 0.8, '#f03b20', 1, '#bd0026'],
					} });
			}
			// Pins: the cluster circle stays (nearly) invisible for clicking; donut markers draw it.
			map.addLayer({ id: `${l.id}-clusters`, type: 'circle', source: l.id, filter: ['has', 'point_count'],
				paint: {
					'circle-color': l.color, 'circle-opacity': colorBy ? 0.01 : 0.8,
					'circle-stroke-color': '#fff', 'circle-stroke-width': colorBy ? 0 : 2,
					'circle-radius': colorBy ? ['step', ['get', 'point_count'], 17, 10, 20, 30, 23, 100, 27]
						: ['step', ['get', 'point_count'], 12, 10, 16, 50, 21, 200, 27],
				} });
			if (!colorBy) {
				map.addLayer({ id: `${l.id}-count`, type: 'symbol', source: l.id, filter: ['has', 'point_count'],
					layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': FONT, 'text-size': 12 },
					paint: { 'text-color': '#ffffff' } });
			}
			map.addLayer({ id: `${l.id}-points`, type: 'circle', source: l.id, filter: ['!', ['has', 'point_count']],
				paint: {
					'circle-color': colorBy ? matchColor(`c__${state.indicator}`, state.indicator) : l.color,
					'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, radius - 1, 14, radius + 2],
					'circle-stroke-color': colorBy ? '#222' : '#fff', 'circle-stroke-width': colorBy ? 1.3 : 1.2,
				} });
			map.addLayer({ id: `${l.id}-selected`, type: 'circle', source: l.id, filter: ['==', ['get', 'fid'], ''],
				paint: { 'circle-radius': radius + 5, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#111', 'circle-stroke-width': 3 } });
		},
		setHeatmap(map, l, on) {
			for (const id of [`${l.id}-heat`]) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
			for (const id of [`${l.id}-clusters`, `${l.id}-count`, `${l.id}-points`]) {
				if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'none' : 'visible');
			}
		},
	};
	if (colorBy) {
		// Cluster counts depend on the indicator, so the source is rebuilt when it changes.
		r.setIndicator = (map, l, indicator, data, state) => {
			const before = map.getStyle().layers.map(x => x.id).find((id, i, all) => i > all.indexOf(`${l.id}-selected`));
			for (const id of ids(l)) if (map.getLayer(id)) map.removeLayer(id);
			map.removeSource(l.id);
			r.add(map, l, data, { ...state, indicator });
			if (before) for (const id of ids(l)) if (map.getLayer(id)) map.moveLayer(id, before);
		};
	}
	return r;
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
