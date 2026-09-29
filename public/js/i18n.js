// Interface strings. Data labels (fields, codes, datasets) come from catalog.json.
const STRINGS = {
	en: {
		title: 'RESOLVE Map',
		switchLang: 'العربية',
		layers: 'Layers',
		basemap: 'Base map',
		close: 'Close',
		legend: 'Legend',
		about: 'About this layer',
		indicator: 'Indicator',
		colouredBy: 'Coloured by the most common answer',
		noData: 'No published answer',
		respondents: 'respondents',
		answered: 'answered',
		loading: 'Loading data…',
		loadFailed: 'Could not load map data.',
		places: 'Areas on the map',
		otherVillages: 'Respondents in other villages of this district',
		otherVillagesNote: (n, v) => `${n} respondents from ${v} villages with fewer than the minimum number of respondents are pooled here.`,
		sensitiveNote: 'Sensitive indicators (income, age, gender, costs) are shown for the whole district only.',
		suppressedFewer: (k) => `Hidden: fewer than ${k} answers`,
		suppressedCells: 'Some small counts are hidden to protect privacy',
		hiddenCount: 'hidden',
		location: 'Location',
		precision: 'Location precision',
		source: 'Source',
		licence: 'Licence',
		method: 'Method',
		caveats: 'Caveats',
		owner: 'Owner',
		consent: 'Consent',
		citation: 'Citation',
		dateFrom: 'From',
		dateTo: 'To',
		dayNight: 'Day / night',
		all: 'All',
		heatmap: 'Show as density',
		surveys: 'Surveys',
		identity: 'Identity (restricted)',
		clusterHint: 'Zoom in to see individual points',
		privacyNote: 'Survey results are summaries of at least 5 respondents per area. No individual answers, names or farm locations are published.',
		researchBanner: 'RESEARCH VIEW — contains personal data. Local use only; do not share screenshots or files.',
		features: (n) => `${n} features`,
		statusOf: 'Answers not counted',
		multiNote: 'several answers possible',
	},
	ar: {
		title: 'خريطة RESOLVE',
		switchLang: 'English',
		layers: 'الطبقات',
		basemap: 'الخريطة الأساسية',
		close: 'إغلاق',
		legend: 'مفتاح الخريطة',
		about: 'عن هذه الطبقة',
		indicator: 'المؤشر',
		colouredBy: 'اللون حسب الإجابة الأكثر شيوعاً',
		noData: 'لا توجد إجابة منشورة',
		respondents: 'مستجيب',
		answered: 'أجابوا',
		loading: 'جارٍ تحميل البيانات…',
		loadFailed: 'تعذّر تحميل بيانات الخريطة.',
		places: 'المناطق على الخريطة',
		otherVillages: 'المستجيبون من قرى أخرى في هذا القضاء',
		otherVillagesNote: (n, v) => `تم تجميع ${n} مستجيباً من ${v} قرى لم يبلغ عدد المستجيبين فيها الحد الأدنى.`,
		sensitiveNote: 'تُعرض المؤشرات الحساسة (الدخل، العمر، الجنس، التكاليف) على مستوى القضاء فقط.',
		suppressedFewer: (k) => `مخفي: أقل من ${k} إجابات`,
		suppressedCells: 'بعض الأعداد الصغيرة مخفية لحماية الخصوصية',
		hiddenCount: 'مخفي',
		location: 'الموقع',
		precision: 'دقة الموقع',
		source: 'المصدر',
		licence: 'الترخيص',
		method: 'المنهجية',
		caveats: 'ملاحظات',
		owner: 'المالك',
		consent: 'الموافقة',
		citation: 'الاستشهاد',
		dateFrom: 'من',
		dateTo: 'إلى',
		dayNight: 'نهار / ليل',
		all: 'الكل',
		heatmap: 'عرض ككثافة',
		surveys: 'الاستبيانات',
		identity: 'الهوية (مقيّد)',
		clusterHint: 'قرّب الخريطة لرؤية النقاط المفردة',
		privacyNote: 'نتائج الاستبيان هي ملخصات لخمسة مستجيبين على الأقل في كل منطقة. لا تُنشر إجابات فردية أو أسماء أو مواقع مزارع.',
		researchBanner: 'عرض بحثي — يحتوي على بيانات شخصية. للاستخدام المحلي فقط؛ لا تشارك لقطات الشاشة أو الملفات.',
		features: (n) => `${n} عنصر`,
		statusOf: 'إجابات غير محتسبة',
		multiNote: 'يمكن اختيار أكثر من إجابة',
	},
};

let lang = 'en';
try { lang = localStorage.getItem('resolve.lang') === 'ar' ? 'ar' : 'en'; } catch { /* storage unavailable */ }

export function getLang() { return lang; }

export function setLang(next) {
	lang = next;
	try { localStorage.setItem('resolve.lang', next); } catch { /* ignore */ }
	document.documentElement.lang = next;
	document.documentElement.dir = next === 'ar' ? 'rtl' : 'ltr';
	for (const node of document.querySelectorAll('[data-i18n]')) node.textContent = t(node.dataset.i18n);
	for (const node of document.querySelectorAll('[data-i18n-title]')) {
		node.title = t(node.dataset.i18nTitle);
		node.setAttribute('aria-label', t(node.dataset.i18nTitle));
	}
}

export function t(key, ...args) {
	const value = STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
	return typeof value === 'function' ? value(...args) : value;
}

// Pick the current language from a {en, ar} label object.
export function label(obj) {
	if (obj === null || obj === undefined) return '';
	if (typeof obj === 'string') return obj;
	return obj[lang] || obj.en || '';
}

export function formatNumber(n) {
	return new Intl.NumberFormat(lang === 'ar' ? 'ar-LB' : 'en-GB').format(n);
}
