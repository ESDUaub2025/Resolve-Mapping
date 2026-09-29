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
			paint: { 'fill-color': matchColor(`mode__${state.indicator}`, state.indicator), 'fill-opacity': 0.72 } });
		map.addLayer({ id: `${l.id}-line`, type: 'line', source: l.id,
			paint: { 'line-color': '#ffffff', 'line-width': 1.2 } });
		map.addLayer({ id: `${l.id}-selected`, type: 'line', source: l.id, filter: ['==', ['get', 'fid'], ''],
			paint: { 'line-color': '#111111', 'line-width': 3 } });
	},
	setIndicator(map, l, indicator) {
		map.setPaintProperty(`${l.id}-fill`, 'fill-color', matchColor(`mode__${indicator}`, indicator));
	},
};

const polygons = {
	layerIds: (l) => [`${l.id}-fill`, `${l.id}-line`, `${l.id}-selected`],
	interactive: (l) => [`${l.id}-fill`],
	add(map, l, data) {
		map.addSource(l.id, { type: 'geojson', data });
		map.addLayer({ id: `${l.id}-fill`, type: 'fill', source: l.id, paint: { 'fill-color': l.color, 'fill-opacity': 0.12 } });
		map.addLayer({ id: `${l.id}-line`, type: 'line', source: l.id, paint: { 'line-color': l.color, 'line-width': 1.5 } });
		map.addLayer({ id: `${l.id}-selected`, type: 'line', source: l.id, filter: ['==', ['get', 'fid'], ''],
			paint: { 'line-color': '#111111', 'line-width': 3 } });
	},
};

function clusteredPoints(radius) {
	return {
		layerIds: (l) => [`${l.id}-clusters`, `${l.id}-count`, `${l.id}-points`, `${l.id}-selected`].concat(l.heatmap ? [`${l.id}-heat`] : []),
		interactive: (l) => [`${l.id}-clusters`, `${l.id}-points`],
		add(map, l, data) {
			map.addSource(l.id, { type: 'geojson', data, cluster: !!l.cluster, clusterRadius: 40, clusterMaxZoom: 13 });
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
					'circle-color': l.color, 'circle-opacity': 0.75, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5,
					'circle-radius': ['step', ['get', 'point_count'], 12, 10, 16, 50, 21, 200, 27],
				} });
			map.addLayer({ id: `${l.id}-count`, type: 'symbol', source: l.id, filter: ['has', 'point_count'],
				layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': FONT, 'text-size': 12 },
				paint: { 'text-color': '#ffffff' } });
			map.addLayer({ id: `${l.id}-points`, type: 'circle', source: l.id, filter: ['!', ['has', 'point_count']],
				paint: { 'circle-color': l.color, 'circle-radius': radius, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2 } });
			map.addLayer({ id: `${l.id}-selected`, type: 'circle', source: l.id, filter: ['==', ['get', 'fid'], ''],
				paint: { 'circle-radius': radius + 4, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#111', 'circle-stroke-width': 3 } });
		},
		setHeatmap(map, l, on) {
			setVisibility(map, [`${l.id}-heat`], on);
			setVisibility(map, [`${l.id}-clusters`, `${l.id}-count`, `${l.id}-points`], !on);
		},
	};
}

export const RENDERERS = {
	survey_summary: surveySummary,
	polygons,
	points: clusteredPoints(5),
	respondents: clusteredPoints(6),
};

export function renderer(layer) {
	const r = RENDERERS[layer.renderer];
	if (!r) throw new Error(`Unknown renderer ${layer.renderer} for layer ${layer.id}`);
	return r;
}

export function setLayerVisible(map, layer, visible, state) {
	const r = renderer(layer);
	setVisibility(map, r.layerIds(layer), visible);
	if (visible && r.setHeatmap) r.setHeatmap(map, layer, !!state.heatmap);
}

export function highlight(map, layers, layerId, featureId) {
	for (const l of layers) {
		const id = `${l.id}-selected`;
		if (map.getLayer(id)) map.setFilter(id, ['==', ['get', 'fid'], l.id === layerId ? featureId : '']);
	}
}
