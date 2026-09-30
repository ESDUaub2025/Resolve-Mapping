// Donut charts for clustered pins: each cluster shows how its pins split across the answers of
// the current indicator (e.g. farmer types), so colours stay readable when pins are grouped.
// Counts come from MapLibre clusterProperties (k0, k1, … per answer code). Markers are purely
// visual (pointer-events: none); clicks still hit the transparent cluster circle layer below.
import { NO_DATA_COLOR } from './catalog.js';

const SVG = 'http://www.w3.org/2000/svg';

function svg(tag, attrs) {
	const node = document.createElementNS(SVG, tag);
	for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
	return node;
}

function donut(counts, colors, total) {
	const r = total >= 100 ? 26 : total >= 30 ? 22 : total >= 10 ? 19 : 16;
	const inner = r * 0.55;
	const size = r * 2 + 2;
	const root = svg('svg', { width: size, height: size, viewBox: `0 0 ${size} ${size}`, role: 'img' });
	const c = size / 2;
	let start = -Math.PI / 2;
	const slices = counts.map((n, i) => [n, colors[i]]).filter(([n]) => n > 0);
	const rest = total - counts.reduce((a, b) => a + b, 0);
	if (rest > 0) slices.push([rest, NO_DATA_COLOR]);
	for (const [n, color] of slices) {
		const angle = (n / total) * Math.PI * 2;
		if (slices.length === 1) {
			root.append(svg('circle', { cx: c, cy: c, r, fill: color }));
		} else {
			const end = start + angle;
			const large = angle > Math.PI ? 1 : 0;
			const p = (a, rad) => `${c + rad * Math.cos(a)} ${c + rad * Math.sin(a)}`;
			root.append(svg('path', {
				d: `M ${p(start, r)} A ${r} ${r} 0 ${large} 1 ${p(end, r)} L ${p(end, inner)} A ${inner} ${inner} 0 ${large} 0 ${p(start, inner)} Z`,
				fill: color,
			}));
			start = end;
		}
	}
	root.append(svg('circle', { cx: c, cy: c, r: inner, fill: '#ffffff' }));
	root.append(svg('circle', { cx: c, cy: c, r, fill: 'none', stroke: '#ffffff', 'stroke-width': 1.5 }));
	const label = svg('text', { x: c, y: c, 'text-anchor': 'middle', 'dominant-baseline': 'central',
		'font-size': r >= 22 ? 12 : 11, 'font-weight': 700, fill: '#222' });
	label.textContent = String(total);
	root.append(label);
	return root;
}

export class ClusterDonuts {
	constructor(map, sourceId) {
		this.map = map;
		this.sourceId = sourceId;
		this.markers = new Map();
		this.codes = [];
		this.colors = [];
		this.enabled = true;
	}

	configure(codes, colors) {
		this.codes = codes;
		this.colors = colors;
		this.clear();
	}

	clear() {
		for (const m of this.markers.values()) m.remove();
		this.markers.clear();
	}

	setEnabled(on) {
		this.enabled = on;
		if (!on) this.clear();
		else this.update();
	}

	update() {
		if (!this.enabled || !this.map.getSource(this.sourceId) || !this.map.isSourceLoaded(this.sourceId)) return;
		const seen = new Set();
		for (const f of this.map.querySourceFeatures(this.sourceId)) {
			const p = f.properties;
			if (!p.cluster) continue;
			const key = `${p.cluster_id}`;
			if (seen.has(key)) continue;
			seen.add(key);
			if (!this.markers.has(key)) {
				const counts = this.codes.map((_, i) => p[`k${i}`] || 0);
				const el = document.createElement('div');
				el.className = 'cluster-donut';
				el.append(donut(counts, this.colors, p.point_count));
				el.setAttribute('aria-hidden', 'true');
				this.markers.set(key, new maplibregl.Marker({ element: el }).setLngLat(f.geometry.coordinates).addTo(this.map));
			}
		}
		for (const [key, m] of this.markers) {
			if (!seen.has(key)) { m.remove(); this.markers.delete(key); }
		}
	}
}
