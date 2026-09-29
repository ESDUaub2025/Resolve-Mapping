// catalog.json is the single description of what the map shows: layers, fields, vocabularies,
// dataset cards. Everything dataset-specific lives there, not in this code.
import { label } from './i18n.js';

// Okabe–Ito (colour-blind safe) for categorical answers. Ordinal scales use viridis, which is
// ordered and neutral: it does not imply that one end of a scale is "good" and the other "bad".
const CATEGORICAL = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9', '#D55E00', '#F0E442', '#000000', '#999999'];
const ORDINAL = ['#fde725', '#5ec962', '#21918c', '#3b528b', '#440154'];
export const NO_DATA_COLOR = '#c8c8c8';

let catalog = null;

export async function loadCatalog() {
	const res = await fetch('data/catalog.json', { cache: 'no-cache' });
	if (!res.ok) throw new Error(`catalog.json: HTTP ${res.status}`);
	catalog = await res.json();
	return catalog;
}

export function getCatalog() { return catalog; }

export function field(code) { return catalog.fields[code]; }
export function fieldLabel(code) { return label(catalog.fields[code]?.label) || code; }
export function vocabOf(code) { const f = catalog.fields[code]; return f && f.vocab ? catalog.vocabularies[f.vocab] : null; }

export function codeLabel(fieldCode, code) {
	const vocab = vocabOf(fieldCode);
	const entry = vocab?.codes.find(c => c.code === code);
	return entry ? label(entry.label) : code;
}

export function statusLabel(status) { return label(catalog.statuses[status]) || status; }
export function precisionLabel(p) { return label(catalog.precisions[p]) || p; }
export function propertyLabel(p) { return label(catalog.property_labels[p]) || fieldLabel(p); }
export function groupLabel(g) { return label(catalog.groups[g]) || g; }

// Colour for each code of a field, in vocabulary order.
export function codeColors(fieldCode) {
	const vocab = vocabOf(fieldCode);
	if (!vocab) return [];
	const codes = vocab.codes.map(c => c.code);
	if (vocab.kind === 'ordinal') {
		// Spread the ordinal ramp across the actual number of levels.
		return codes.map((code, i) => [code, ORDINAL[Math.round(i * (ORDINAL.length - 1) / Math.max(1, codes.length - 1))]]);
	}
	return codes.map((code, i) => [code, CATEGORICAL[i % CATEGORICAL.length]]);
}
