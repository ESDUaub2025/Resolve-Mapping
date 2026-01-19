(function() {
	// Map of cluster icon colors per thematic key
	const clusterColors = {
		water: '#1abc9c',
		energy: '#f39c12',
		food: '#9b59b6',
		general: '#2980b9',
		regen: '#27ae60',
		fire: '#e74c3c',
		farmers: '#16a085'  // Teal color for farmers layer
	};

	// --- I18N ---
	const i18n = {
		lang: (localStorage.getItem('uiLang') || 'en'),
		strings: {
			en: {
				controls: 'Controls', baseMap: 'Base map', layers: 'Layers', aiLayers: 'AI Analysis Layers', details: 'Details',
				basemap: { osm: 'Streets (OSM)', esri: 'Satellite (Esri)', 'carto-light': 'Carto Light', 'carto-dark': 'Carto Dark', opentopo: 'OpenTopo' },
				layerNames: { water: 'Water', energy: 'Energy', food: 'Food', general: 'General', regen: 'Regenerative Ag', preservations: 'Preservations', firePoints: 'Fire points', heatmap: 'Fire density (deck.gl)', farmers: 'Farmers Survey', aiRegen: 'Regenerative Adoption', aiWater: 'Water Risk', aiEcon: 'Economic Resilience', aiLabor: 'Labor Availability', aiClimate: 'Climate Vulnerability' },
				layerDescriptions: {
					aiRegen: '<b>Factors:</b> Village, Farm Size, Soil Type, Water Source, Regen Knowledge, Income Source.<br><b>Accuracy:</b> ~61% (based on survey).<br><b>Importance:</b> Identifies farmers likely to adopt sustainable practices.',
					aiWater: '<b>Factors:</b> Village, Soil Type, Water Source, Irrigation Frequency, Scarcity Months, Energy Source.<br><b>Accuracy:</b> ~98% (High confidence).<br><b>Importance:</b> Highlights areas vulnerable to water shortages.',
					aiEcon: '<b>Factors:</b> Farm Size, Income Source, Marketing Challenges, Machinery, Coop Member, Energy Source.<br><b>Accuracy:</b> Composite Score.<br><b>Importance:</b> Targets vulnerable farmers for support.',
					aiLabor: '<b>Factors:</b> Village, Farm Size, Main Workers, Machinery, Main Crops, Income Source.<br><b>Accuracy:</b> ~85% (Estimated).<br><b>Importance:</b> Identifies areas with potential labor shortages.',
					aiClimate: '<b>Factors:</b> Village, Water Source, Soil Type, Main Crops, Pest Management, Regen Knowledge.<br><b>Accuracy:</b> ~90% (Estimated).<br><b>Importance:</b> Highlights areas most vulnerable to climate change impacts.'
				},
				hint: 'Data loads automatically. Toggle layers and click pins to view details on the right.',
				enableFilters: 'Enable filters',
				filterLabels: {
					villageContains: 'Village contains', cropContains: 'Crop contains', irrigSource: 'Irrigation source', waterSuff: 'Water sufficiency', scarcityRange: 'Scarcity month range (1-12)', irrigFreq: 'Irrigation freq contains',
					energySource: 'Energy source', hasSolar: 'Has solar', hasDiesel: 'Has diesel/generator', peakRange: 'Peak energy amount (min/max)',
					productionLevel: 'Production level', tradProducts: 'Traditional products contains', hasAnimals: 'Has animals', birdsRange: 'Bird count (min/max)', cropsContains: 'Crops contains',
					farmSize: 'Farm size', soilType: 'Soil type', climateObserved: 'Climate change observed', changeKeywords: 'Change keywords', impactContains: 'Impact contains',
					techniques: 'Techniques contains', amendments: 'Amendments contains', fertilRel: 'Fertilizer reliance', pestMgmt: 'Pest management', pesticRel: 'Pesticide reliance',
					acqDateRange: 'Acquisition date range', dayNight: 'Day/Night', timeRange: 'Time range', latRange: 'Latitude range', lonRange: 'Longitude range',
					nameContains: 'Name contains', typeCategory: 'Type/Category', areaRange: 'Area (min/max)',
					farmerVillage: 'Village', farmerCrops: 'Main Crops', farmerFarmSize: 'Farm Size', farmerSoilType: 'Soil Type', farmerWaterSource: 'Water Source', farmerEnergySource: 'Energy Source', farmerRegenPractices: 'Regenerative Agriculture'
				}
			},
			ar: {
				controls: 'التحكم', baseMap: 'الخريطة الأساسية', layers: 'الطبقات', aiLayers: 'طبقات الذكاء الاصطناعي', details: 'التفاصيل',
				basemap: { osm: 'شوارع (OSM)', esri: 'صورة فضائية (Esri)', 'carto-light': 'كارطو فاتح', 'carto-dark': 'كارطو داكن', opentopo: 'OpenTopo' },
				layerNames: { water: 'المياه', energy: 'الطاقة', food: 'الغذاء', general: 'عام', regen: 'الزراعة التجديدية', preservations: 'المحميات', firePoints: 'نقاط الحرائق', heatmap: 'كثافة الحرائق', farmers: 'استبيان المزارعين', aiRegen: 'تبني الزراعة التجديدية', aiWater: 'مخاطر الأمن المائي', aiEcon: 'المرونة الاقتصادية', aiLabor: 'توفر العمالة', aiClimate: 'الضعف المناخي' },
				layerDescriptions: {
					aiRegen: '<b>العوامل:</b> القرية، حجم المزرعة، نوع التربة، مصدر المياه، المعرفة بالتجديدية، مصدر الدخل.<br><b>الدقة:</b> ~61% (بناءً على المسح).<br><b>الأهمية:</b> تحديد المزارعين المحتمل تبنيهم للممارسات المستدامة.',
					aiWater: '<b>العوامل:</b> القرية، نوع التربة، مصدر المياه، وتيرة الري، أشهر الشح، مصدر الطاقة.<br><b>الدقة:</b> ~98% (ثقة عالية).<br><b>الأهمية:</b> تسليط الضوء على المناطق المعرضة لنقص المياه.',
					aiEcon: '<b>العوامل:</b> حجم المزرعة، مصدر الدخل، تحديات التسويق، الآلات، عضوية التعاونية، مصدر الطاقة.<br><b>الدقة:</b> مؤشر مركب.<br><b>الأهمية:</b> استهداف المزارعين الأكثر ضعفاً للدعم.',
					aiLabor: '<b>العوامل:</b> القرية، حجم المزرعة، العمال الرئيسيون، الآلات، المحاصيل الرئيسية، مصدر الدخل.<br><b>الدقة:</b> ~85% (تقديري).<br><b>الأهمية:</b> تحديد المناطق التي تعاني من نقص محتمل في العمالة.',
					aiClimate: '<b>العوامل:</b> القرية، مصدر المياه، نوع التربة، المحاصيل الرئيسية، مكافحة الآفات، المعرفة بالتجديدية.<br><b>الدقة:</b> ~90% (تقديري).<br><b>الأهمية:</b> تسليط الضوء على المناطق الأكثر عرضة لتأثيرات تغير المناخ.'
				},
				hint: 'تُحمّل البيانات تلقائيًا. فعّل الطبقات واضغط على العلامات لعرض التفاصيل على اليمين.',
				enableFilters: 'تفعيل المرشحات',
				filterLabels: {
					villageContains: 'اسم القرية يحتوي', cropContains: 'المحصول يحتوي', irrigSource: 'مصدر مياه الريّ', waterSuff: 'توفر المياه', scarcityRange: 'أشهر الشح (1-12)', irrigFreq: 'وتيرة الري تحتوي',
					energySource: 'مصدر الطاقة', hasSolar: 'يوجد طاقة شمسية', hasDiesel: 'يوجد ديزل/مولد', peakRange: 'كمية الذروة (حد أدنى/أقصى)',
					productionLevel: 'مستوى الإنتاج', tradProducts: 'المنتجات التقليدية تحتوي', hasAnimals: 'يوجد حيوانات', birdsRange: 'عدد الطيور (حد أدنى/أقصى)', cropsContains: 'المحاصيل تحتوي',
					farmSize: 'حجم الزراعة', soilType: 'نوع التربة', climateObserved: 'هل لوحظ تغير مناخي', changeKeywords: 'كلمات مفتاحية للتغير', impactContains: 'التأثير يحتوي',
					techniques: 'التقنيات تحتوي', amendments: 'المحسّنات تحتوي', fertilRel: 'الاعتماد على الأسمدة', pestMgmt: 'مكافحة الآفات', pesticRel: 'الاعتماد على المبيدات',
					acqDateRange: 'نطاق تاريخ الرصد', dayNight: 'نهار/ليل', timeRange: 'نطاق الوقت', latRange: 'نطاق خط العرض', lonRange: 'نطاق خط الطول',
					nameContains: 'الاسم يحتوي', typeCategory: 'النوع/التصنيف', areaRange: 'المساحة (حد أدنى/أقصى)',
					farmerVillage: 'القرية', farmerCrops: 'المحاصيل الرئيسية', farmerFarmSize: 'حجم المزرعة', farmerSoilType: 'نوع التربة', farmerWaterSource: 'مصدر المياه', farmerEnergySource: 'مصدر الطاقة', farmerRegenPractices: 'الزراعة التجديدية'
				}
			}
		},
		setLang(next) { this.lang = next; localStorage.setItem('uiLang', next); this.apply(); },
		apply() {
			const S = this.strings[this.lang];
			// static labels
			const setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
			setText('i18n-controls', S.controls);
			setText('i18n-base-map', S.baseMap);
			setText('i18n-basemap-osm', S.basemap.osm);
			setText('i18n-basemap-esri', S.basemap.esri);
			setText('i18n-basemap-carto-light', S.basemap['carto-light']);
			setText('i18n-basemap-carto-dark', S.basemap['carto-dark']);
			setText('i18n-basemap-opentopo', S.basemap.opentopo);
			setText('i18n-layers', S.layers);
			setText('i18n-layer-water', S.layerNames.water);
			setText('i18n-layer-energy', S.layerNames.energy);
			setText('i18n-layer-food', S.layerNames.food);
			setText('i18n-layer-general', S.layerNames.general);
			setText('i18n-layer-regen', S.layerNames.regen);
			setText('i18n-layer-fire-points', S.layerNames.firePoints);
			const presLabel = document.getElementById('i18n-layer-preservations'); if (presLabel) presLabel.textContent = S.layerNames.preservations;
			setText('i18n-layer-farmers', S.layerNames.farmers);
			setText('i18n-heatmap', S.layerNames.heatmap);
			setText('i18n-ai-layers', S.aiLayers);
			setText('i18n-ai-regen', S.layerNames.aiRegen);
			setText('i18n-ai-water', S.layerNames.aiWater);
			setText('i18n-ai-econ', S.layerNames.aiEcon);
			setText('i18n-ai-labor', S.layerNames.aiLabor);
			setText('i18n-ai-climate', S.layerNames.aiClimate);
			
			// Set descriptions (using innerHTML for formatting)
			const setHtml = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
			if (S.layerDescriptions) {
				setHtml('desc-ai-regen', S.layerDescriptions.aiRegen);
				setHtml('desc-ai-water', S.layerDescriptions.aiWater);
				setHtml('desc-ai-econ', S.layerDescriptions.aiEcon);
				setHtml('desc-ai-labor', S.layerDescriptions.aiLabor);
				setHtml('desc-ai-climate', S.layerDescriptions.aiClimate);
			}

			setText('i18n-hint', S.hint);
			setText('i18n-details-title', S.details);
			
			// dir + lang toggle label
			const root = document.documentElement;
			root.setAttribute('lang', this.lang === 'ar' ? 'ar' : 'en');
			root.setAttribute('dir', this.lang === 'ar' ? 'rtl' : 'ltr');
			
			// Update language toggle button text (both locations if present)
			const langBtn = document.getElementById('lang-toggle');
			const langToggleText = document.getElementById('lang-toggle-text');
			const langText = (this.lang === 'ar') ? 'EN' : 'AR';
			if (langBtn && !langToggleText) {
				// Old style - just button with text
				langBtn.textContent = langText;
			}
			if (langToggleText) {
				// New style - button with separate text span
				langToggleText.textContent = langText;
			}
			
			// Update navbar title
			const navbarTitle = document.getElementById('navbar-title');
			if (navbarTitle) {
				navbarTitle.textContent = this.lang === 'ar' 
					? 'خريطة البيانات الزراعية في لبنان'
					: 'Lebanon Agricultural Data Map';
			}
			
			// Update controls text in navbar
			const navbarControlsText = document.getElementById('navbar-controls-text');
			if (navbarControlsText) {
				navbarControlsText.textContent = S.controls;
			}
			
			// dynamic filter labels and enable text
			Object.entries(filterUIById).forEach(([id, ui]) => {
				const enableLabel = ui.enable && ui.enable.nextSibling; // associated label node
				if (enableLabel && enableLabel.nodeType === Node.ELEMENT_NODE) enableLabel.textContent = S.enableFilters;
				// Update filter control labels where possible by class 'filter-label'
				const labels = ui.controls ? ui.controls.querySelectorAll('.filter-label') : [];
				const orderMap = {
					'water-points': [S.filterLabels.villageContains, S.filterLabels.cropContains, S.filterLabels.irrigSource, S.filterLabels.waterSuff, S.filterLabels.scarcityRange, S.filterLabels.irrigFreq],
					'energy-points': [S.filterLabels.villageContains, S.filterLabels.energySource, S.filterLabels.hasSolar, S.filterLabels.hasDiesel, S.filterLabels.peakRange],
					'food-points': [S.filterLabels.villageContains, S.filterLabels.productionLevel, S.filterLabels.tradProducts, S.filterLabels.hasAnimals, S.filterLabels.birdsRange, S.filterLabels.cropsContains],
					'general-points': [S.filterLabels.villageContains, S.filterLabels.farmSize, S.filterLabels.soilType, S.filterLabels.climateObserved, S.filterLabels.changeKeywords, S.filterLabels.impactContains],
					'regen-points': [S.filterLabels.villageContains, S.filterLabels.techniques, S.filterLabels.amendments, S.filterLabels.fertilRel, S.filterLabels.pestMgmt, S.filterLabels.pesticRel],
					'fire-points': [S.filterLabels.acqDateRange, S.filterLabels.dayNight, S.filterLabels.timeRange, S.filterLabels.latRange, S.filterLabels.lonRange]
				};
				const texts = orderMap[id] || [];
				labels.forEach((el, idx) => { if (texts[idx]) el.textContent = texts[idx]; });
			});
			
			// Update filter dropdown options to match new language
			refreshFilterOptions();
		}
	};
	// --- Path base resolver ---
	// CONFIGURATION: Set this to your S3/R2 URL for production (e.g. 'https://pub-xxx.r2.dev/my-project/'), or leave null for local/relative
	const PRODUCTION_DATA_URL = null; 

	const qsBase = new URLSearchParams(location.search).get('base');
	const APP_BASE_URL = (qsBase && (qsBase.endsWith('/') ? qsBase : (qsBase + '/'))) || (window.APP_BASE_URL || '');
	let ROOT_BASE = APP_BASE_URL || (new URL('.', (document.currentScript && document.currentScript.src) || location.href).href);
	// If we somehow computed a file:// base while running under http(s), correct it to http(s)
	if (/^file:/i.test(ROOT_BASE) && /^https?:/i.test(location.protocol)) {
		ROOT_BASE = new URL('.', location.href).href;
	}
	function fromRoot(path) {
		try {
			const p = (path || '').replace(/^\/+/, '');
			
			// If a production data URL is set, use it for data/ and output/ folders
			if (PRODUCTION_DATA_URL && (p.startsWith('data/') || p.startsWith('output/'))) {
				const base = PRODUCTION_DATA_URL.endsWith('/') ? PRODUCTION_DATA_URL : (PRODUCTION_DATA_URL + '/');
				return base + p;
			}

			// Preserve tile template placeholders so MapLibre can substitute {z}/{x}/{y}
			if (p.indexOf('{') !== -1 || p.indexOf('}') !== -1) {
				const base = ROOT_BASE.endsWith('/') ? ROOT_BASE : (ROOT_BASE + '/');
				return base + p;
			}
			return new URL(p, ROOT_BASE).toString();
		} catch (e) { return path; }
	}

	
	// --- Filtering state ---
	const originalDataBySource = {}; // id -> FeatureCollection
	const sourceUrlById = {}; // id -> url used to load
	const filterEnabledById = {}; // id -> boolean
	const activeFiltersById = {}; // id -> { key: value }
	const filterUIById = {}; // id -> { container, controls, enable }

	let clusterIconHandlerInstalled = false;
	const map = new maplibregl.Map({
		container: 'map',
		style: {
			version: 8,
			glyphs: 'https://demotiles.maplibre.org/fonts/{fontstack}/{range}.pbf',
			sources: {
				osm: {
					type: 'raster',
					tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
					tileSize: 256,
					attribution: '© OpenStreetMap contributors'
				},
				esri: {
					type: 'raster',
					tiles: ['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
					tileSize: 256,
					attribution: 'Esri World Imagery'
				}
			},
			layers: [
				{ id: 'osm', type: 'raster', source: 'osm' },
				{ id: 'esri', type: 'raster', source: 'esri', layout: { visibility: 'none' } }
			]
		},
		center: [35.6, 33.7],
		zoom: 9
	});

	map.addControl(new maplibregl.NavigationControl({ showZoom: true }), 'top-left');

	// deck.gl overlay holder (used to restrict tile requests to ROI)
	let deckOverlay = null;

	// --- Icon utilities (inline SVGs for sidebar and rasterized images for map) ---

	function setLabelIcon(id, svg) {
		const el = document.getElementById(id);
		if (el) el.innerHTML = svg;
	}

	const iconSvgs = {
		water: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#1abc9c" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#1abc9c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2C12 2 5 9 5 15a7 7 0 0 0 14 0c0-6-7-13-7-13z"/></svg>`,
	  
		energy: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#f39c12" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#f39c12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>`,
	  
		food: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#9b59b6" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#9b59b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 3C10 5.5 8 8 8 11a4 4 0 0 0 8 0c0-3-2-5.5-4-8z"/><path fill="none" stroke="#9b59b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M7 21c5-3 8-3 10 0"/></svg>`,
	  
		general: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#2980b9" stroke-width="1.5" opacity="0.95"/><circle fill="none" stroke="#2980b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" cx="12" cy="12" r="10"/><line fill="none" stroke="#2980b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" x1="12" y1="8" x2="12" y2="8"/><path fill="none" stroke="#2980b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M11 12h2v4h-2z"/></svg>`,
	  
		regen: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#27ae60" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#27ae60" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M2 12a10 10 0 1 0 10-10"/><polyline fill="none" stroke="#27ae60" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="2,2 2,12 12,12"/></svg>`,
	  
		fire: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#e74c3c" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#e74c3c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 2C9 6 16 8 12 14c-2 3-7 1-7-3 0-5 5-9 7-9z"/><path fill="none" stroke="#e74c3c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 22c4 0 7-3 7-7 0-6-7-13-7-13"/></svg>`,
		preservations: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#2ecc71" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#2ecc71" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M12 3l8 4v6c0 5-4 8-8 8s-8-3-8-8V7l8-4z"/><path fill="none" stroke="#2ecc71" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4"/></svg>`,
		farmers: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#16a085" stroke-width="1.5" opacity="0.95"/><path fill="none" stroke="#16a085" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle fill="none" stroke="#16a085" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" cx="12" cy="7" r="4"/></svg>`,
		aiRegen: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#27ae60" stroke-width="1.5" opacity="0.95"/><path fill="#27ae60" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>`,
		aiWater: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#e74c3c" stroke-width="1.5" opacity="0.95"/><path fill="#e74c3c" d="M12 2L1 21h22L12 2zm1 16h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>`,
		aiEcon: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#f39c12" stroke-width="1.5" opacity="0.95"/><path fill="#f39c12" d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>`,
		aiLabor: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#9b59b6" stroke-width="1.5" opacity="0.95"/><path fill="#9b59b6" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>`,
		aiClimate: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="white" stroke="#3498db" stroke-width="1.5" opacity="0.95"/><path fill="#3498db" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg>`
	  };
	  

	function installSidebarIcons() {
		setLabelIcon('icon-water', iconSvgs.water);
		setLabelIcon('icon-energy', iconSvgs.energy);
		setLabelIcon('icon-food', iconSvgs.food);
		setLabelIcon('icon-general', iconSvgs.general);
		setLabelIcon('icon-regen', iconSvgs.regen);
		setLabelIcon('icon-fire', iconSvgs.fire);
		setLabelIcon('icon-fire-pts', iconSvgs.fire);
		setLabelIcon('icon-preservations', iconSvgs.preservations);
		setLabelIcon('icon-farmers', iconSvgs.farmers);
		setLabelIcon('icon-ai-regen', iconSvgs.aiRegen);
		setLabelIcon('icon-ai-water', iconSvgs.aiWater);
		setLabelIcon('icon-ai-econ', iconSvgs.aiEcon);
		setLabelIcon('icon-ai-labor', iconSvgs.aiLabor);
		setLabelIcon('icon-ai-climate', iconSvgs.aiClimate);
	}

	function ensureMapImage(map, idKey, svg) {
		const imageId = `${idKey}-img`;
		if (map.hasImage(imageId)) return imageId;
		if (!svg) return null;
		const enlarged = svg.replace('width="16" height="16"', 'width="24" height="24"');
		const blob = new Blob([enlarged], { type: 'image/svg+xml' });
		const url = URL.createObjectURL(blob);
		const img = new Image(24, 24);
		img.onload = () => {
			const canvas = document.createElement('canvas');
			canvas.width = 24; canvas.height = 24;
			const ctx = canvas.getContext('2d');
			ctx.drawImage(img, 0, 0, 24, 24);
			map.addImage(imageId, ctx.getImageData(0, 0, 24, 24));
			URL.revokeObjectURL(url);
		};
		img.src = url;
		return imageId;
	}

	// Track hovered feature ids per layer for clean state toggling
	const hoveredByLayer = {};

	function addPolygonLayer(id, url, fillColor) {
		sourceUrlById[id] = url;
		if (!map.getSource(id)) {
			map.addSource(id, { 
				type: 'geojson', 
				data: url,
				promoteId: 'id'  // Use stable feature IDs instead of generateId
			});
		}
		const fillId = `${id}-fill`;
		const outlineId = `${id}-outline`;
		if (!map.getLayer(fillId)) {
			map.addLayer({
				id: fillId,
				type: 'fill',
				source: id,
				layout: { visibility: 'none' },
				paint: {
					'fill-color': fillColor,
					'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.35, 0.18]
				}
			});
		}
		if (!map.getLayer(outlineId)) {
			map.addLayer({
				id: outlineId,
				type: 'line',
				source: id,
				layout: { visibility: 'none' },
				paint: {
					'line-color': fillColor,
					'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 2.0, 1.0]
				}
			});
		}
	}

	function bindPolygonInteraction(id) {
		const fillId = `${id}-fill`;
		map.on('mousemove', fillId, (e) => {
			const prev = hoveredByLayer[fillId];
			if (prev != null) {
				map.setFeatureState({ source: id, id: prev }, { hover: false });
			}
			const f = e.features && e.features[0];
			if (f && f.id != null) {
				hoveredByLayer[fillId] = f.id;
				map.setFeatureState({ source: id, id: f.id }, { hover: true });
			}
		});
		map.on('mouseleave', fillId, () => {
			const prev = hoveredByLayer[fillId];
			if (prev != null) map.setFeatureState({ source: id, id: prev }, { hover: false });
		});
		map.on('click', fillId, (e) => {
			openDetailsFromEvent(e.lngLat, e.point);
		});
		map.on('mouseenter', fillId, () => map.getCanvas().style.cursor = 'pointer');
		map.on('mouseleave', fillId, () => map.getCanvas().style.cursor = '');
	}

	// --- Sidebar collapse ---
	function setupSidebarCollapse() {
		const btn = document.getElementById('sidebar-toggle');
		const sidebar = document.getElementById('sidebar');
		if (!btn || !sidebar) return;

		const setAria = () => {
			const isCollapsed = sidebar.classList.contains('collapsed');
			const expanded = (!isCollapsed).toString();
			btn.setAttribute('aria-expanded', expanded);
			btn.setAttribute('aria-controls', 'sidebar');
			btn.setAttribute('aria-label', isCollapsed ? 'Show sidebar' : 'Hide sidebar');
		};

		const toggle = () => {
			sidebar.classList.toggle('collapsed');
			setAria();
		};

		btn.addEventListener('click', toggle);
		setAria();
		
		// Sidebar should be visible by default
		sidebar.classList.remove('collapsed');
		setAria();
	}


	function addGeoJsonLayer(id, dataOrUrl, color, shouldCluster = true) {
		if (map.getSource(id)) return;
		
		// Support both URL strings (legacy) and GeoJSON objects (new)
		const isUrl = typeof dataOrUrl === 'string';
		if (isUrl) {
			sourceUrlById[id] = dataOrUrl;
		}
		
		const pixelOffsets = {
			'water-points': [0, 0],
			'energy-points': [12, 12],
			'food-points': [-12, -12],
			'general-points': [12, -12],
			'regen-points': [-12, 12],
			'fire-points-raw': [0, 14],
			'farmers-points': [14, 0]
		};
		
		// Add source (use generateId for legacy URLs, promoteId for canonical data)
		const sourceConfig = { 
			type: 'geojson', 
			data: dataOrUrl, 
			cluster: shouldCluster, 
			clusterRadius: 40, 
			clusterMaxZoom: 14 
		};
		
		if (!isUrl) {
			// Canonical data with stable IDs
			sourceConfig.promoteId = 'featureId';
		} else {
			// Legacy URL-based data
			sourceConfig.generateId = true;
		}
		
		map.addSource(id, sourceConfig);
		map.addLayer({
			id: id,
			type: 'circle',
			source: id,
			paint: {
				'circle-radius': 0,
				'circle-color': color,
				'circle-opacity': 0,
				'circle-stroke-color': '#ffffff',
				'circle-stroke-width': 0
			}
		});

		// For fire raw points, skip symbols/bubbles/clusters; used only as heatmap source
		if (id === 'fire-points-raw') {
			return;
		}

		// Bubble underlay drawn first
		const bubbleId = `${id}-bubble`;
		if (!map.getLayer(bubbleId)) {
			map.addLayer({
				id: bubbleId,
				type: 'circle',
				source: id,
				layout: { visibility: 'none' },
				filter: ['!', ['has', 'point_count']],
				paint: {
					'circle-radius': [
						'interpolate', ['linear'], ['zoom'],
						6, ['case', ['boolean', ['feature-state', 'hover'], false], 10, 7],
						12, ['case', ['boolean', ['feature-state', 'hover'], false], 16, 12]
					],
					'circle-color': color,
					'circle-opacity': [
						'case', ['boolean', ['feature-state', 'hover'], false], 0.35, 0.18
					],
					'circle-translate': pixelOffsets[id] || [0, 0],
					'circle-translate-anchor': 'viewport'
				}
			});
		}

		// Icon symbol layer
		const iconKeyByLayer = {
			'water-points': 'water',
			'energy-points': 'energy',
			'food-points': 'food',
			'general-points': 'general',
			'regen-points': 'regen',
			'fire-points-raw': 'fire',
			'fire-points': 'fire',
			'farmers-points': 'farmers'
		};
		const key = iconKeyByLayer[id];
		if (key) {
			const imageId = ensureMapImage(map, key, iconSvgs[key]);
			const symbolId = `${id}-symbols`;
			if (!map.getLayer(symbolId)) {
				map.addLayer({
					id: symbolId,
					type: 'symbol',
					source: id,
					filter: ['!', ['has', 'point_count']],
					layout: {
						'icon-image': `${key}-img`,
						'icon-size': [
							'interpolate', ['linear'], ['zoom'],
							6, 0.8,
							12, 1.2
						],
						'icon-allow-overlap': true,
						'icon-ignore-placement': true,
						'visibility': 'none'
					},
					paint: {
						'icon-translate': pixelOffsets[id] || [0, 0],
						'icon-translate-anchor': 'viewport',
						'icon-opacity': [
							'case', ['boolean', ['feature-state', 'hover'], false], 1, 0.9
						]
					}
				});
			}
		}

		// Cluster visualization (circles + count) for clustered sources
		const clustersId = `${id}-clusters`;
		const clusterCountId = `${id}-cluster-count`;
		if (shouldCluster && !map.getLayer(clustersId)) {
			map.addLayer({
				id: clustersId,
				type: 'circle',
				source: id,
				filter: ['has', 'point_count'],
				layout: { visibility: 'none' },
				paint: {
					'circle-color': color,
					'circle-opacity': 0.25,
					'circle-stroke-color': color,
					'circle-stroke-width': 2,
					'circle-radius': [
						'interpolate', ['linear'], ['get', 'point_count'],
						2, 16,
						25, 22,
						100, 28
					]
				}
			});
		}

		if (shouldCluster && !map.getLayer(clusterCountId)) {
			map.addLayer({
				id: clusterCountId,
				type: 'symbol',
				source: id,
				filter: ['has', 'point_count'],
				layout: {
					// Use dynamic icon composed from key and count to avoid glyphs
					'icon-image': [
						'concat',
						['literal', 'cluster-'],
						['case',
							['==', id, 'water-points'], 'water',
							['==', id, 'energy-points'], 'energy',
							['==', id, 'food-points'], 'food',
							['==', id, 'general-points'], 'general',
							['==', id, 'regen-points'], 'regen',
							['==', id, 'fire-points'], 'fire',
							['==', id, 'farmers-points'], 'farmers',
							'gen'
						],
						['literal', '-'],
						['to-string', ['get', 'point_count']]
					],
					'icon-size': [
						'interpolate', ['linear'], ['get', 'point_count'],
						2, 0.8,
						25, 1.0,
						100, 1.2
					],
					'icon-allow-overlap': true,
					'icon-ignore-placement': true,
					'visibility': 'none'
				},
				paint: {}
			});
		}
	}

	// Add canonical bilingual layer (new architecture)
	function addCanonicalLayer(layerId, themeData) {
		if (!themeData || !themeData.data) {
			console.error(`Cannot add canonical layer ${layerId}: missing theme data`);
			return;
		}
		
		const { id, color, data } = themeData;
		
		// Apply coordinate staggering to prevent overlapping points in same village
		const staggeredData = {
			type: 'FeatureCollection',
			features: staggerDuplicateCoordinates(data.features),
			metadata: data.metadata
		};
		
		// Add source using GeoJSON object directly (not URL)
		addGeoJsonLayer(layerId, staggeredData, color, true);
		
		// Store reference for filtering (with staggered coordinates)
		originalDataBySource[layerId] = staggeredData;
		
		// Update layer count badge
		updateLayerCount(layerId, staggeredData.features.length);
		
		console.log(`✓ Added canonical layer: ${layerId} (${staggeredData.features.length} features, staggered)`);
	}

	async function preloadGeoJson(id) {
		try {
			const url = sourceUrlById[id];
			if (!url) return;
			const res = await fetch(url);
			if (!res.ok) return;
			const fc = await res.json();
			if (fc && fc.type === 'FeatureCollection') {
				// Apply coordinate staggering for farmers data to prevent overlap
				if (id === 'farmers-points') {
					fc.features = staggerDuplicateCoordinates(fc.features);
				}
				originalDataBySource[id] = fc;
			}
		} catch {}
	}

	// Stagger points with duplicate coordinates in a circular pattern
	function staggerDuplicateCoordinates(features) {
		const coordMap = new Map(); // Map of "lng,lat" -> array of feature indices
		
		// Group features by coordinate
		features.forEach((feature, idx) => {
			if (feature.geometry && feature.geometry.type === 'Point') {
				const coords = feature.geometry.coordinates;
				const key = `${coords[0]},${coords[1]}`;
				if (!coordMap.has(key)) {
					coordMap.set(key, []);
				}
				coordMap.get(key).push(idx);
			}
		});
		
		// Apply circular offset pattern to duplicates
		coordMap.forEach((indices, coordKey) => {
			if (indices.length > 1) {
				// Multiple features at same location - stagger them
				const [lng, lat] = coordKey.split(',').map(Number);
				const offsetDistance = 0.0002; // ~22 meters at this latitude
				
				indices.forEach((idx, position) => {
					if (position === 0) return; // Keep first one at original position
					
					// Calculate angle for circular arrangement
					const angle = (position / indices.length) * 2 * Math.PI;
					const radius = offsetDistance * Math.ceil(position / 8); // Expand spiral for many duplicates
					
					// Apply offset
					const newLng = lng + (radius * Math.cos(angle));
					const newLat = lat + (radius * Math.sin(angle));
					
					features[idx].geometry.coordinates = [newLng, newLat];
				});
			}
		});
		
		return features;
	}

	function cleanTextValue(v) {
		if (v == null) return '';
		const s = String(v).trim();
		const idx = s.indexOf(':');
		if (idx >= 0 && idx < s.length - 1) return s.slice(idx + 1).trim();
		return s;
	}

	function includesArabicInsensitive(haystack, needle) {
		if (!needle) return true;
		const h = (haystack || '').toString().toLowerCase();
		const n = needle.toString().toLowerCase();
		return h.indexOf(n) !== -1;
	}

	function parseNumberFromText(v) {
		if (v == null) return null;
		const s = String(v);
		const digits = s.match(/[0-9]+([\.,][0-9]+)?/);
		if (!digits) return null;
		const n = parseFloat(digits[0].replace(',', '.'));
		return isNaN(n) ? null : n;
	}

	function findFirstProp(obj, candidates) {
		for (const k of candidates) {
			if (Object.prototype.hasOwnProperty.call(obj, k)) return k;
		}
		return null;
	}

	// Comprehensive bilingual value grouping mappings for cleaner filter options
	const valueGroupings = {
		'water-points': {
			'القرية': {
				'area_1': {
					en: 'Area 1',
					ar: 'منطقة 1',
					patterns: ['منطقة 1', 'area 1', '1', 'الأولى', 'first']
				},
				'area_2': {
					en: 'Area 2', 
					ar: 'منطقة 2',
					patterns: ['منطقة 2', 'area 2', '2', 'الثانية', 'second']
				},
				'area_3': {
					en: 'Area 3',
					ar: 'منطقة 3', 
					patterns: ['منطقة 3', 'area 3', '3', 'الثالثة', 'third']
				},
				'other_areas': {
					en: 'Other areas',
					ar: 'مناطق أخرى',
					patterns: ['منطقة', 'area', 'قرية', 'village', 'مزرعة', 'farm', 'أخرى', 'other', 'مكان']
				}
			},
			'المحصول': {
				'wheat': {
					en: 'Wheat',
					ar: 'قمح',
					patterns: ['قمح', 'wheat', 'حنطة', 'برّ']
				},
				'barley': {
					en: 'Barley',
					ar: 'شعير',
					patterns: ['شعير', 'barley']
				},
				'corn': {
					en: 'Corn/Maize',
					ar: 'ذرة',
					patterns: ['ذرة', 'corn', 'maize', 'ذره']
				},
				'tomato': {
					en: 'Tomato',
					ar: 'طماطم',
					patterns: ['طماطم', 'tomato', 'بندورة', 'طماطة']
				},
				'cucumber': {
					en: 'Cucumber',
					ar: 'خيار',
					patterns: ['خيار', 'cucumber', 'قثاء']
				},
				'olive': {
					en: 'Olive',
					ar: 'زيتون',
					patterns: ['زيتون', 'olive', 'زيت']
				},
				'citrus': {
					en: 'Citrus fruits',
					ar: 'حمضيات',
					patterns: ['حمضيات', 'citrus', 'برتقال', 'orange', 'ليمون', 'lemon', 'جريب فروت']
				},
				'vegetables': {
					en: 'Mixed vegetables',
					ar: 'خضروات متنوعة',
					patterns: ['خضروات', 'vegetables', 'خضار', 'متنوعة', 'mixed']
				},
				'legumes': {
					en: 'Legumes',
					ar: 'بقوليات',
					patterns: ['بقوليات', 'legumes', 'فول', 'beans', 'عدس', 'lentils', 'حمص', 'chickpeas']
				},
				'other_crops': {
					en: 'Other crops',
					ar: 'محاصيل أخرى',
					patterns: ['أخرى', 'other', 'متنوع', 'مختلف', 'various', 'غير محدد', 'unknown', 'لا أعرف']
				}
			},
			'ريّ المحصول': {
				'daily': {
					en: 'Daily irrigation',
					ar: 'ري يومي',
					patterns: ['يومي', 'daily', 'كل يوم', 'everyday', 'يوميا']
				},
				'weekly': {
					en: 'Weekly irrigation',
					ar: 'ري أسبوعي',
					patterns: ['أسبوعي', 'weekly', 'كل أسبوع', 'أسبوعيا', 'مرة في الأسبوع']
				},
				'bi_weekly': {
					en: 'Bi-weekly irrigation',
					ar: 'ري كل أسبوعين',
					patterns: ['أسبوعين', 'bi-weekly', 'كل أسبوعين', 'مرتين في الشهر']
				},
				'monthly': {
					en: 'Monthly irrigation',
					ar: 'ري شهري',
					patterns: ['شهري', 'monthly', 'كل شهر', 'شهريا', 'مرة في الشهر']
				},
				'seasonal': {
					en: 'Seasonal irrigation',
					ar: 'ري موسمي',
					patterns: ['موسمي', 'seasonal', 'حسب الموسم', 'فصلي']
				},
				'irregular': {
					en: 'Irregular irrigation',
					ar: 'ري غير منتظم',
					patterns: ['غير منتظم', 'irregular', 'متقطع', 'حسب الحاجة', 'as needed']
				},
				'other_frequency': {
					en: 'Other/Unknown',
					ar: 'أخرى/غير محدد',
					patterns: ['أخرى', 'other', 'غير محدد', 'unknown', 'لا أعرف', 'متنوع', 'مختلف']
				}
			},
			'مصدر مياه الريّ الرئيسي': {
				'well_water': {
					en: 'Well water',
					ar: 'مياه الآبار',
					patterns: ['بئر', 'آبار', 'المياه الجوفية', 'مياه جوفية', 'بئر ارتوازي', 'بئر عادي', 'بئر محفور', 'حفر بئر', 'آبار جوفية']
				},
				'spring_water': {
					en: 'Spring water',
					ar: 'مياه الينابيع',
					patterns: ['نبع', 'عين', 'ينبوع', 'عيون مياه', 'نبع طبيعي', 'عين ماء', 'ينابيع', 'مياه العيون']
				},
				'river_stream': {
					en: 'River/Stream',
					ar: 'مياه الأنهار',
					patterns: ['نهر', 'مجرى مائي', 'مجرى', 'نهر صغير', 'وادي', 'مجاري المياه', 'أنهار', 'مياه الوادي']
				},
				'rainwater': {
					en: 'Rainwater',
					ar: 'مياه الأمطار',
					patterns: ['مياه أمطار', 'أمطار', 'مياه المطر', 'تجميع المطر', 'حصاد المطر', 'مياه الأمطار', 'تخزين المطر']
				},
				'tank_storage': {
					en: 'Tank/Storage',
					ar: 'خزانات المياه',
					patterns: ['خزان', 'خزانات', 'تخزين المياه', 'خزان مياه', 'صهريج', 'برك تخزين', 'خزانات أرضية']
				},
				'network_municipal': {
					en: 'Network/Municipal',
					ar: 'شبكة المياه العامة',
					patterns: ['شبكة', 'شبكة المياه', 'مياه الشبكة', 'مياه عامة', 'بلدية', 'مياه البلدية', 'الشبكة العامة']
				},
				'other_unknown': {
					en: 'Other/Unknown',
					ar: 'أخرى/غير محدد',
					patterns: ['أخرى', 'غير محدد', 'غير معروف', 'متنوع', 'مختلط', 'other', 'unknown', 'لا أعرف', 'غير واضح']
				}
			},
			'توفر المياه': {
				'sufficient': {
					en: 'Sufficient',
					ar: 'كافي',
					patterns: ['كافي', 'كافية', 'جيد', 'جيدة', 'متوفر', 'متوفرة', 'وافر', 'وافرة', 'مناسب', 'مناسبة']
				},
				'insufficient': {
					en: 'Insufficient',
					ar: 'غير كافي',
					patterns: ['غير كافي', 'غير كافية', 'نقص', 'قليل', 'قليلة', 'ضعيف', 'ضعيفة', 'محدود', 'محدودة']
				},
				'seasonal': {
					en: 'Seasonal',
					ar: 'موسمي',
					patterns: ['موسمي', 'موسمية', 'متغير', 'متغيرة', 'حسب الموسم', 'يختلف', 'متقلب', 'غير منتظم']
				}
			}
		},
		'energy-points': {
			'القرية': {
				'area_1': {
					en: 'Area 1',
					ar: 'منطقة 1',
					patterns: ['منطقة 1', 'area 1', '1', 'الأولى', 'first']
				},
				'area_2': {
					en: 'Area 2', 
					ar: 'منطقة 2',
					patterns: ['منطقة 2', 'area 2', '2', 'الثانية', 'second']
				},
				'area_3': {
					en: 'Area 3',
					ar: 'منطقة 3', 
					patterns: ['منطقة 3', 'area 3', '3', 'الثالثة', 'third']
				},
				'other_areas': {
					en: 'Other areas',
					ar: 'مناطق أخرى',
					patterns: ['منطقة', 'area', 'قرية', 'village', 'مزرعة', 'farm', 'أخرى', 'other', 'مكان']
				}
			},
			'مصدر الطاقة الرئيسي': {
				'solar': {
					en: 'Solar power',
					ar: 'طاقة شمسية',
					patterns: ['شمس', 'الشمس', 'طاقة شمسية', 'ألواح شمسية', 'solar', 'شمسي', 'الطاقة الشمسية', 'لوح شمسي']
				},
				'diesel_generator': {
					en: 'Diesel/Generator',
					ar: 'ديزل/مولد',
					patterns: ['ديزل', 'مولد', 'مازوت', 'generator', 'مولد ديزل', 'مولد كهربائي', 'مولدات', 'محرك ديزل']
				},
				'grid_network': {
					en: 'Electrical grid',
					ar: 'الشبكة الكهربائية',
					patterns: ['شبكة', 'شبكة كهرباء', 'كهرباء عامة', 'التيار العام', 'الشبكة العامة', 'كهرباء الدولة']
				},
				'battery': {
					en: 'Battery storage',
					ar: 'بطاريات',
					patterns: ['بطارية', 'بطاريات', 'تخزين', 'battery', 'مراكم', 'خزن الطاقة']
				},
				'wind': {
					en: 'Wind power',
					ar: 'طاقة الرياح',
					patterns: ['رياح', 'طاقة الرياح', 'wind', 'توربين رياح', 'مولد رياح', 'طواحين الهواء']
				},
				'hybrid_mixed': {
					en: 'Hybrid/Mixed',
					ar: 'مختلط/متنوع',
					patterns: ['مختلط', 'متنوع', 'أكثر من مصدر', 'hybrid', 'مدمج', 'متعدد المصادر']
				},
				'other_unknown': {
					en: 'Other/Unknown',
					ar: 'أخرى/غير محدد',
					patterns: ['أخرى', 'غير محدد', 'غير معروف', 'other', 'unknown', 'لا أعرف']
				}
			}
		},
		'food-points': {
			'القرية': {
				'village_a': {
					en: 'Village A',
					ar: 'قرية أ',
					patterns: ['قرية أ', 'village a', 'قريةأ', 'القرية الأولى']
				},
				'village_b': {
					en: 'Village B', 
					ar: 'قرية ب',
					patterns: ['قرية ب', 'village b', 'قريةب', 'القرية الثانية']
				},
				'village_c': {
					en: 'Village C',
					ar: 'قرية ج', 
					patterns: ['قرية ج', 'village c', 'قريةج', 'القرية الثالثة']
				},
				'other_village': {
					en: 'Other villages',
					ar: 'قرى أخرى',
					patterns: ['قرية', 'village', 'قري', 'مزرعة', 'farm', 'منطقة', 'area', 'أخرى', 'other']
				}
			},
			'المنتجات التقليدية الرئيسية': {
				'dairy': {
					en: 'Dairy products',
					ar: 'منتجات الألبان',
					patterns: ['ألبان', 'dairy', 'حليب', 'milk', 'جبن', 'cheese', 'لبن', 'زبدة', 'butter']
				},
				'poultry': {
					en: 'Poultry products',
					ar: 'منتجات الدواجن',
					patterns: ['دواجن', 'poultry', 'دجاج', 'chicken', 'بيض', 'eggs', 'ديك رومي', 'turkey']
				},
				'meat': {
					en: 'Meat products',
					ar: 'منتجات اللحوم',
					patterns: ['لحوم', 'meat', 'لحم', 'أغنام', 'sheep', 'ماعز', 'goat', 'أبقار', 'cattle']
				},
				'grains': {
					en: 'Grain products',
					ar: 'منتجات الحبوب',
					patterns: ['حبوب', 'grains', 'قمح', 'wheat', 'شعير', 'barley', 'ذرة', 'corn', 'أرز', 'rice']
				},
				'vegetables': {
					en: 'Fresh vegetables',
					ar: 'خضروات طازجة',
					patterns: ['خضروات', 'vegetables', 'خضار', 'طازجة', 'fresh']
				},
				'fruits': {
					en: 'Fresh fruits',
					ar: 'فواكه طازجة',
					patterns: ['فواكه', 'fruits', 'فاكهة', 'طازجة', 'fresh']
				},
				'processed': {
					en: 'Processed foods',
					ar: 'أغذية مصنعة',
					patterns: ['مصنعة', 'processed', 'محفوظة', 'preserved', 'معلبة', 'canned']
				},
				'other_products': {
					en: 'Other products',
					ar: 'منتجات أخرى',
					patterns: ['أخرى', 'other', 'متنوعة', 'various', 'مختلفة', 'different']
				}
			},
			'المحصولين الرئيسيين': {
				'wheat_barley': {
					en: 'Wheat & Barley',
					ar: 'قمح وشعير',
					patterns: ['قمح وشعير', 'wheat barley', 'قمح شعير', 'حنطة شعير']
				},
				'corn_wheat': {
					en: 'Corn & Wheat',
					ar: 'ذرة وقمح',
					patterns: ['ذرة وقمح', 'corn wheat', 'ذرة قمح']
				},
				'tomato_cucumber': {
					en: 'Tomato & Cucumber',
					ar: 'طماطم وخيار',
					patterns: ['طماطم وخيار', 'tomato cucumber', 'طماطم خيار', 'بندورة خيار']
				},
				'olive_citrus': {
					en: 'Olive & Citrus',
					ar: 'زيتون وحمضيات',
					patterns: ['زيتون وحمضيات', 'olive citrus', 'زيتون حمضيات']
				},
				'vegetables_mixed': {
					en: 'Mixed vegetables',
					ar: 'خضروات متنوعة',
					patterns: ['خضروات متنوعة', 'mixed vegetables', 'خضار مختلطة']
				},
				'legumes_grains': {
					en: 'Legumes & Grains',
					ar: 'بقوليات وحبوب',
					patterns: ['بقوليات وحبوب', 'legumes grains', 'بقوليات حبوب']
				},
				'other_combinations': {
					en: 'Other combinations',
					ar: 'تركيبات أخرى',
					patterns: ['أخرى', 'other', 'متنوع', 'مختلف', 'various', 'different']
				}
			},
			'مستوى الانتاج': {
				'high': {
					en: 'High production',
					ar: 'إنتاج عالي',
					patterns: ['عالي', 'عالية', 'مرتفع', 'مرتفعة', 'جيد', 'جيدة', 'ممتاز', 'ممتازة', 'كبير', 'كبيرة']
				},
				'medium': {
					en: 'Medium production',
					ar: 'إنتاج متوسط',
					patterns: ['متوسط', 'متوسطة', 'وسط', 'معتدل', 'معتدلة', 'مقبول', 'مقبولة']
				},
				'low': {
					en: 'Low production',
					ar: 'إنتاج منخفض',
					patterns: ['منخفض', 'منخفضة', 'ضعيف', 'ضعيفة', 'قليل', 'قليلة', 'محدود', 'محدودة']
				}
			}
		},
		'general-points': {
			'القرية': {
				'village_a': {
					en: 'Village A',
					ar: 'قرية أ',
					patterns: ['قرية أ', 'village a', 'قريةأ', 'القرية الأولى']
				},
				'village_b': {
					en: 'Village B', 
					ar: 'قرية ب',
					patterns: ['قرية ب', 'village b', 'قريةب', 'القرية الثانية']
				},
				'village_c': {
					en: 'Village C',
					ar: 'قرية ج', 
					patterns: ['قرية ج', 'village c', 'قريةج', 'القرية الثالثة']
				},
				'other_village': {
					en: 'Other villages',
					ar: 'قرى أخرى',
					patterns: ['قرية', 'village', 'قري', 'مزرعة', 'farm', 'منطقة', 'area', 'أخرى', 'other']
				}
			},
			'حجم الزراعة': {
				'small': {
					en: 'Small farm',
					ar: 'زراعة صغيرة',
					patterns: ['صغير', 'صغيرة', 'قليل', 'قليلة', 'محدود', 'محدودة', 'بسيط', 'بسيطة']
				},
				'medium': {
					en: 'Medium farm',
					ar: 'زراعة متوسطة',
					patterns: ['متوسط', 'متوسطة', 'وسط', 'معتدل', 'معتدلة', 'مقبول', 'مقبولة']
				},
				'large': {
					en: 'Large farm',
					ar: 'زراعة كبيرة',
					patterns: ['كبير', 'كبيرة', 'واسع', 'واسعة', 'ممتد', 'ممتدة', 'ضخم', 'ضخمة']
				}
			},
			'نوع التربة': {
				'clay': {
					en: 'Clay soil',
					ar: 'تربة طينية',
					patterns: ['طين', 'طينية', 'clay', 'أرض طينية', 'تربة طين', 'طيني']
				},
				'sandy': {
					en: 'Sandy soil',
					ar: 'تربة رملية',
					patterns: ['رمل', 'رملية', 'sandy', 'أرض رملية', 'تربة رمل', 'رملي']
				},
				'loamy': {
					en: 'Loamy soil',
					ar: 'تربة طميية',
					patterns: ['طمي', 'طميية', 'loam', 'أرض طميية', 'تربة طمي', 'طميي']
				},
				'rocky': {
					en: 'Rocky soil',
					ar: 'تربة صخرية',
					patterns: ['صخري', 'صخرية', 'حجري', 'حجرية', 'rocky', 'صخور', 'حجارة']
				},
				'mixed': {
					en: 'Mixed soil',
					ar: 'تربة مختلطة',
					patterns: ['مختلط', 'متنوع', 'mixed', 'أكثر من نوع', 'مدمج', 'متعدد']
				},
				'other_unknown': {
					en: 'Other/Unknown',
					ar: 'أخرى/غير محدد',
					patterns: ['أخرى', 'غير محدد', 'غير معروف', 'other', 'unknown', 'لا أعرف']
				}
			}
		},
		'regen-points': {
			'القرية': {
				'village_a': {
					en: 'Village A',
					ar: 'قرية أ',
					patterns: ['قرية أ', 'village a', 'قريةأ', 'القرية الأولى']
				},
				'village_b': {
					en: 'Village B', 
					ar: 'قرية ب',
					patterns: ['قرية ب', 'village b', 'قريةب', 'القرية الثانية']
				},
				'village_c': {
					en: 'Village C',
					ar: 'قرية ج', 
					patterns: ['قرية ج', 'village c', 'قريةج', 'القرية الثالثة']
				},
				'other_village': {
					en: 'Other villages',
					ar: 'قرى أخرى',
					patterns: ['قرية', 'village', 'قري', 'مزرعة', 'farm', 'منطقة', 'area', 'أخرى', 'other']
				}
			},
			'الاعتماد على الاسمدة الكيميائية': {
				'high_dependency': {
					en: 'High dependency',
					ar: 'اعتماد عالي',
					patterns: ['عالي', 'عالية', 'كثير', 'كثيرة', 'اعتماد كبير', 'بشكل كبير', 'اعتماد شديد']
				},
				'medium_dependency': {
					en: 'Medium dependency',
					ar: 'اعتماد متوسط',
					patterns: ['متوسط', 'متوسطة', 'معتدل', 'معتدلة', 'أحياناً', 'بين الحين والآخر']
				},
				'low_dependency': {
					en: 'Low dependency',
					ar: 'اعتماد قليل',
					patterns: ['قليل', 'قليلة', 'منخفض', 'منخفضة', 'اعتماد قليل', 'نادراً', 'قليل الاستخدام']
				},
				'no_dependency': {
					en: 'No dependency',
					ar: 'بدون اعتماد',
					patterns: ['لا', 'لا يوجد', 'بدون', 'غير مستخدم', 'لا أستخدم', 'عدم الاستخدام']
				}
			},
			'مكافحة الآفات': {
				'chemical': {
					en: 'Chemical control',
					ar: 'مكافحة كيميائية',
					patterns: ['كيميائي', 'كيميائية', 'مبيد', 'مبيدات', 'chemical', 'المبيدات الكيميائية']
				},
				'biological': {
					en: 'Biological control',
					ar: 'مكافحة حيوية',
					patterns: ['حيوي', 'حيوية', 'بيولوجي', 'biological', 'طبيعي', 'طبيعية', 'المكافحة الحيوية']
				},
				'integrated': {
					en: 'Integrated control',
					ar: 'مكافحة متكاملة',
					patterns: ['متكامل', 'متكاملة', 'مختلط', 'integrated', 'مدمج', 'المكافحة المتكاملة']
				},
				'manual': {
					en: 'Manual control',
					ar: 'مكافحة يدوية',
					patterns: ['يدوي', 'يدوية', 'manual', 'إزالة يدوية', 'باليد', 'المكافحة اليدوية']
				}
			},
			'الاعتماد على المبيدات الكيميائية': {
				'high_dependency': {
					en: 'High dependency',
					ar: 'اعتماد عالي',
					patterns: ['عالي', 'عالية', 'كثير', 'كثيرة', 'اعتماد كبير', 'بشكل كبير']
				},
				'medium_dependency': {
					en: 'Medium dependency',
					ar: 'اعتماد متوسط',
					patterns: ['متوسط', 'متوسطة', 'معتدل', 'معتدلة', 'أحياناً']
				},
				'low_dependency': {
					en: 'Low dependency',
					ar: 'اعتماد قليل',
					patterns: ['قليل', 'قليلة', 'منخفض', 'منخفضة', 'نادراً']
				},
				'no_dependency': {
					en: 'No dependency',
					ar: 'بدون اعتماد',
					patterns: ['لا', 'لا يوجد', 'بدون', 'غير مستخدم', 'عدم الاستخدام']
				}
			}
		},
		'preservations-poly': {
			'NAME': {
				'reserve_a': {
					en: 'Nature Reserve A',
					ar: 'محمية طبيعية أ',
					patterns: ['محمية أ', 'reserve a', 'المحمية الأولى', 'nature reserve a']
				},
				'reserve_b': {
					en: 'Nature Reserve B',
					ar: 'محمية طبيعية ب',
					patterns: ['محمية ب', 'reserve b', 'المحمية الثانية', 'nature reserve b']
				},
				'park_a': {
					en: 'National Park A',
					ar: 'حديقة وطنية أ',
					patterns: ['حديقة أ', 'park a', 'منتزه أ', 'national park a']
				},
				'forest_reserve': {
					en: 'Forest Reserve',
					ar: 'محمية غابات',
					patterns: ['محمية غابات', 'forest reserve', 'غابة محمية', 'حراج محمي']
				},
				'wildlife_sanctuary': {
					en: 'Wildlife Sanctuary',
					ar: 'محمية الحياة البرية',
					patterns: ['محمية حياة برية', 'wildlife sanctuary', 'محمية حيوانات', 'حياة برية']
				},
				'other_areas': {
					en: 'Other protected areas',
					ar: 'مناطق محمية أخرى',
					patterns: ['أخرى', 'other', 'منطقة محمية', 'protected area', 'محمية']
				}
			},
			'DESIG,DESIG_TYPE,GOV_TYPE': {
				'national_park': {
					en: 'National Park',
					ar: 'حديقة وطنية',
					patterns: ['National Park', 'حديقة وطنية', 'منتزه وطني', 'حديقة', 'منتزه']
				},
				'nature_reserve': {
					en: 'Nature Reserve',
					ar: 'محمية طبيعية',
					patterns: ['Nature Reserve', 'محمية طبيعية', 'محمية', 'طبيعية', 'Reserve']
				},
				'protected_area': {
					en: 'Protected Area',
					ar: 'منطقة محمية',
					patterns: ['Protected Area', 'منطقة محمية', 'منطقة حماية', 'Protected', 'محمية']
				},
				'forest_reserve': {
					en: 'Forest Reserve',
					ar: 'محمية غابات',
					patterns: ['Forest Reserve', 'محمية غابات', 'غابة محمية', 'Forest', 'غابة']
				},
				'wildlife_sanctuary': {
					en: 'Wildlife Sanctuary',
					ar: 'محمية الحياة البرية',
					patterns: ['Wildlife Sanctuary', 'محمية الحياة البرية', 'محمية حيوانات', 'Wildlife', 'حياة برية']
				}
			}
		}
	};

	function groupValue(layerId, propKey, rawValue) {
		const layerGroups = valueGroupings[layerId];
		if (!layerGroups) return rawValue;
		
		const propGroups = layerGroups[propKey];
		if (!propGroups) return rawValue;
		
		// Find which group this value belongs to
		for (const [groupKey, groupData] of Object.entries(propGroups)) {
			if (groupData.patterns) {
				for (const pattern of groupData.patterns) {
					if (includesArabicInsensitive(rawValue, pattern)) {
						// Return the localized label based on current language
						return groupData[i18n.lang] || groupData.en;
					}
				}
			}
		}
		
		// If no specific group found, check if we have a generic "other/unknown" group
		if (propGroups.other_unknown) {
			return propGroups.other_unknown[i18n.lang] || propGroups.other_unknown.en;
		}
		
		return rawValue; // Return original if no group found
	}

	function matchesGroupedValue(layerId, propKey, rawValue, selectedGroupValue) {
		// Direct match first
		if (includesArabicInsensitive(rawValue, selectedGroupValue)) {
			return true;
		}
		
		// Check if the selectedGroupValue is a group name that matches this raw value
		const layerGroups = valueGroupings[layerId];
		if (!layerGroups) return false;
		
		const propGroups = layerGroups[propKey];
		if (!propGroups) return false;
		
		// Find the group that matches the selected value (in either language)
		for (const [groupKey, groupData] of Object.entries(propGroups)) {
			if (groupData.en === selectedGroupValue || groupData.ar === selectedGroupValue) {
				// Check if raw value matches any pattern in this group
				if (groupData.patterns) {
					for (const pattern of groupData.patterns) {
						if (includesArabicInsensitive(rawValue, pattern)) {
							return true;
						}
					}
				}
			}
		}
		
		return false;
	}

	function uniqueValues(id, propCandidates, transform) {
		// Try canonical data first (from StateStore)
		const themes = StateStore.getAllThemes();
		const currentLang = StateStore.getLanguage();
		
		// Find theme data for this layer ID
		let data = null;
		for (const [key, theme] of Object.entries(themes)) {
			if (theme.id === id) {
				data = theme.data;
				break;
			}
		}
		
		// Fallback to originalDataBySource for non-canonical layers (fire, farmers, preservations)
		if (!data) {
			data = originalDataBySource[id];
		}
		
		if (!data) return [];
		
		const set = new Set();
		for (const f of data.features || []) {
			const props = f.properties || {};
			
			// Check if this is canonical format (has values.lang structure)
			if (props.values && props.values[currentLang]) {
				// Canonical bilingual format
				const langValues = props.values[currentLang];
				const key = findFirstProp(langValues, propCandidates);
				if (!key) continue;
				const raw = cleanTextValue(langValues[key]);
				if (!raw) continue;
				
				// Apply grouping before transform
				const grouped = groupValue(id, key, raw);
				const val = transform ? transform(grouped) : grouped;
				if (val) set.add(val);
			} else {
				// Legacy format (flat properties)
				const key = findFirstProp(props, propCandidates);
				if (!key) continue;
				const raw = cleanTextValue(props[key]);
				if (!raw) continue;
				
				// Apply grouping before transform
				const grouped = groupValue(id, key, raw);
				const val = transform ? transform(grouped) : grouped;
				if (val) set.add(val);
			}
		}
		return Array.from(set).slice(0, 200);
	}

	function refreshFilterOptions() {
		// Update all multiselect dropdowns to show options in the current language
		Object.entries(filterUIById).forEach(([id, ui]) => {
			if (!ui.controls) return;
			
			const selects = ui.controls.querySelectorAll('select[multiple]');
			selects.forEach(select => {
				// Store current selections (in both languages to maintain state)
				const selectedValues = [];
				for (const option of select.options) {
					if (option.selected && option.value) {
						selectedValues.push(option.value);
					}
				}
				
				// Get the property key for this select (we need to identify which property this select represents)
				const selectContainer = select.parentElement;
				const labelElement = selectContainer.querySelector('.filter-label');
				if (!labelElement) return;
				
				const labelText = labelElement.textContent;
				let propKey = null;
				
				// Map labels to property keys (this is a bit hacky but necessary)
				const labelToPropMap = {
					// Water filters
					'Village': 'القرية',
					'قرية': 'القرية',
					'Crop type': 'المحصول',
					'نوع المحصول': 'المحصول',
					'Irrigation source': 'مصدر مياه الريّ الرئيسي',
					'مصدر مياه الريّ الرئيسي': 'مصدر مياه الريّ الرئيسي',
					'Water sufficiency': 'توفر المياه',
					'توفر المياه': 'توفر المياه',
					'Irrigation frequency': 'ريّ المحصول',
					'تكرار الري': 'ريّ المحصول',
					// Energy filters  
					'Energy source': 'مصدر الطاقة الرئيسي',
					'مصدر الطاقة الرئيسي': 'مصدر الطاقة الرئيسي',
					// Food filters
					'Production level': 'مستوى الانتاج',
					'مستوى الانتاج': 'مستوى الانتاج',
					'Traditional products': 'المنتجات التقليدية الرئيسية',
					'منتجات تقليدية': 'المنتجات التقليدية الرئيسية',
					'Main crops': 'المحصولين الرئيسيين',
					'المحاصيل الرئيسية': 'المحصولين الرئيسيين',
					// General filters
					'Farm size': 'حجم الزراعة',
					'حجم الزراعة': 'حجم الزراعة',
					'Soil type': 'نوع التربة',
					'نوع التربة': 'نوع التربة',
					// Regen filters
					'Fertilizer reliance': 'الاعتماد على الاسمدة الكيميائية',
					'الاعتماد على الاسمدة الكيميائية': 'الاعتماد على الاسمدة الكيميائية',
					'Pest management': 'مكافحة الآفات',
					'مكافحة الآفات': 'مكافحة الآفات',
					'Pesticide reliance': 'الاعتماد على المبيدات الكيميائية',
					'الاعتماد على المبيدات الكيميائية': 'الاعتماد على المبيدات الكيميائية',
					// Preservation filters
					'Protected area name': 'NAME',
					'اسم المنطقة المحمية': 'NAME',
					'Type/Category': 'DESIG,DESIG_TYPE,GOV_TYPE',
					'النوع/التصنيف': 'DESIG,DESIG_TYPE,GOV_TYPE'
				};
				
				propKey = labelToPropMap[labelText];
				if (!propKey) return;
				
				// Get fresh values in the current language
				const newValues = uniqueValues(id, [propKey]);
				
				// Clear and repopulate select
				select.innerHTML = '';
				const emptyOption = document.createElement('option');
				emptyOption.value = '';
				emptyOption.textContent = '(none)';
				select.appendChild(emptyOption);
				
				newValues.forEach(value => {
					const option = document.createElement('option');
					option.value = value;
					option.textContent = value;
					
					// Try to restore selection by checking if this value was selected
					// We need to check both the current value and its equivalent in the other language
					let shouldSelect = selectedValues.includes(value);
					
					if (!shouldSelect && valueGroupings[id] && valueGroupings[id][propKey]) {
						// Check if this value corresponds to a previously selected value in the other language
						const propGroups = valueGroupings[id][propKey];
						for (const [groupKey, groupData] of Object.entries(propGroups)) {
							if (groupData.en === value || groupData.ar === value) {
								// Check if the other language version was selected
								const otherLangValue = (groupData.en === value) ? groupData.ar : groupData.en;
								if (selectedValues.includes(otherLangValue)) {
									shouldSelect = true;
									break;
								}
							}
						}
					}
					
					if (shouldSelect) {
						option.selected = true;
					}
					
					select.appendChild(option);
				});
				
				// Trigger change event to update filters if needed
				if (selectedValues.length > 0) {
					select.dispatchEvent(new Event('change'));
				}
			});
		});
	}

	function getOrInit(obj, key, factory) {
		if (!obj[key]) obj[key] = factory();
		return obj[key];
	}

	function applyFiltersForLayer(id) {
		// Try canonical data first
		const themes = StateStore.getAllThemes();
		const currentLang = StateStore.getLanguage();
		let themeData = null;
		
		// Find theme data for this layer ID
		for (const [key, theme] of Object.entries(themes)) {
			if (theme.id === id) {
				themeData = theme;
				break;
			}
		}
		
		// Fallback to originalDataBySource for non-canonical layers
		const fc = themeData ? themeData.data : originalDataBySource[id];
		const src = map.getSource(id);
		if (!fc || !src) return;
		
		if (!filterEnabledById[id]) {
			// Reset to original
			try { 
				src.setData(fc); 
				updateLayerCount(id, fc.features.length);
			} catch {}
			return;
		}
		
		const filters = activeFiltersById[id] || {};
		let filtered = fc.features.filter((f) => {
			const props = f.properties || {};
			
			// Helper to get property value (works with both canonical and legacy formats)
			const getProp = (cands) => {
				// Check if canonical format
				if (props.values && props.values[currentLang]) {
					const langValues = props.values[currentLang];
					const key = findFirstProp(langValues, cands);
					return key ? cleanTextValue(langValues[key]) : '';
				}
				// Legacy format
				const key = findFirstProp(props, cands);
				return key ? cleanTextValue(props[key]) : '';
			};
			
			// Common selectors
			if (filters.villageNames && filters.villageNames.size) {
				const v = getProp(['القرية', 'القرية:', '4.القرية', '4.القرية:', 'Village', '4. Village']);
				let ok = false;
				for (const val of filters.villageNames) { if (matchesGroupedValue(id, 'القرية', v, val)) { ok = true; break; } }
				if (!ok) return false;
			}
			if (filters.latMin != null || filters.latMax != null) {
				const y = parseFloat(getProp(['Y','y','Latitude','LATITUDE']));
				if (!isNaN(filters.latMin) && !(y >= filters.latMin)) return false;
				if (!isNaN(filters.latMax) && !(y <= filters.latMax)) return false;
			}
			if (filters.lonMin != null || filters.lonMax != null) {
				const x = parseFloat(getProp(['X','x','Longitude','LONGITUDE','lng','lon']));
				if (!isNaN(filters.lonMin) && !(x >= filters.lonMin)) return false;
				if (!isNaN(filters.lonMax) && !(x <= filters.lonMax)) return false;
			}
			
			// Per-layer specifics (using canonical property keys)
			if (id === 'water-points') {
				if (filters.irrigSource && filters.irrigSource.size) {
					const v = getProp(['_6', 'مصدر مياه الريّ الرئيسي', '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟', '13. Water Source']);
					let ok = false;
					for (const val of filters.irrigSource) { if (matchesGroupedValue(id, '_6', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.waterSuff && filters.waterSuff.size) {
					const v = getProp(['_7', 'توفر المياه', '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟', '16. Water Availability']);
					let ok = false; for (const val of filters.waterSuff) { if (matchesGroupedValue(id, '_7', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.scarcityMonthMin || filters.scarcityMonthMax) {
					const t = getProp(['_8', ' أشهر شح المياه']);
					const nums = (t.match(/[0-9]{1,2}/g) || []).map(n=>parseInt(n,10)).filter(n=>n>=1&&n<=12);
					if (nums.length) {
						const mn = isNaN(filters.scarcityMonthMin)?1:filters.scarcityMonthMin;
						const mx = isNaN(filters.scarcityMonthMax)?12:filters.scarcityMonthMax;
						let any = false; for (const n of nums) { if (n>=mn && n<=mx) { any = true; break; } }
						if (!any) return false;
					}
				}
				if (filters.cropTypes && filters.cropTypes.size) {
					const v = getProp(['المحصول', '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟', '10. Main Crops']);
					let ok = false;
					for (const val of filters.cropTypes) { if (matchesGroupedValue(id, 'المحصول', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.irrigFreq && filters.irrigFreq.size) {
					const v = getProp(['_5', 'ريّ المحصول']);
					let ok = false;
					for (const val of filters.irrigFreq) {
						if (matchesGroupedValue(id, '_5', v, val)) {
							ok = true; break;
						}
					}
					if (!ok) return false;
				}
			}
			if (id === 'preservations-poly') {
				if (filters.areaNames && filters.areaNames.size) {
					const name = (props.NAME || props.ORIG_NAME || '').toString();
					let ok = false;
					for (const val of filters.areaNames) { if (matchesGroupedValue(id, 'NAME', name, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.typeCat && filters.typeCat.size) {
					const v = [props.DESIG, props.DESIG_TYPE, props.GOV_TYPE].map(cleanTextValue).join(' | ');
					let ok = false; for (const val of filters.typeCat) { if (matchesGroupedValue(id, 'DESIG,DESIG_TYPE,GOV_TYPE', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.areaMin != null || filters.areaMax != null) {
					const rep = parseNumberFromText(props.REP_AREA);
					const gis = parseNumberFromText(props.GIS_AREA);
					const area = (rep != null ? rep : gis);
					if (area != null) {
						if (!isNaN(filters.areaMin) && !(area >= filters.areaMin)) return false;
						if (!isNaN(filters.areaMax) && !(area <= filters.areaMax)) return false;
					}
				}
			}
			if (id === 'energy-points') {
				if (filters.energySource && filters.energySource.size) {
					const v = getProp(['_3', 'مصدر الطاقة الرئيسي', '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟', '14. Energy Source']);
					let ok = false; for (const val of filters.energySource) { if (matchesGroupedValue(id, '_3', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.hasSolar === true) {
					const v = getProp(['_3', 'مصدر الطاقة الرئيسي', '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟', '14. Energy Source']);
					if (!(/شمس|الشمس|solar|طاقة شمسية/i).test(v)) return false;
				}
				if (filters.hasDiesel === true) {
					const v = getProp(['_3', 'مصدر الطاقة الرئيسي', '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟', '14. Energy Source']);
					if (!(/ديزل|مولد|مازوت|generator/i).test(v)) return false;
				}
				if (filters.peakMin != null || filters.peakMax != null) {
					const v = getProp(['_4', 'كمية الطاقة المستخدمة خلال موسم الذروة ']);
					const n = parseNumberFromText(v);
					if (n != null) {
						if (!isNaN(filters.peakMin) && !(n >= filters.peakMin)) return false;
						if (!isNaN(filters.peakMax) && !(n <= filters.peakMax)) return false;
					}
				}
			}
			if (id === 'food-points') {
				if (filters.production && filters.production.size) {
					const v = getProp(['_5', 'مستوى الانتاج']);
					let ok = false; for (const val of filters.production) { if (matchesGroupedValue(id, '_5', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.tradProducts && filters.tradProducts.size) {
					const v = getProp(['_6', 'المنتجات التقليدية الرئيسية','المتنجات التقليدية الرئيسية']);
					let ok = false;
					for (const val of filters.tradProducts) { if (matchesGroupedValue(id, '_6', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.hasAnimals === true) {
					const v = getProp(['_8', 'انواع الحيوانات:','انواع الحيوانات']);
					const has = v && !/^\s*لا\s*$/i.test(v);
					if (!has) return false;
				}
				if (filters.birdsMin != null || filters.birdsMax != null) {
					const n = parseNumberFromText(getProp(['_9', 'عدد الطيور']));
					if (n != null) {
						if (!isNaN(filters.birdsMin) && !(n >= filters.birdsMin)) return false;
						if (!isNaN(filters.birdsMax) && !(n <= filters.birdsMax)) return false;
					}
				}
				if (filters.mainCrops && filters.mainCrops.size) {
					const v = getProp(['_3', 'المحصولين الرئيسيين',' المحصول الاول والمحصول الثاني']);
					let ok = false;
					for (const val of filters.mainCrops) { if (matchesGroupedValue(id, '_3', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
			}
			if (id === 'general-points') {
				if (filters.farmSize && filters.farmSize.size) {
					const v = getProp(['_3', 'حجم الزراعة', '8.ما هو حجم الحيازة الزراعية الخاصة بك؟', '8. Farm Size']);
					let ok = false; for (const val of filters.farmSize) { if (matchesGroupedValue(id, '_3', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.soilType && filters.soilType.size) {
					const v = getProp(['_4', 'نوع التربة', '9.ما هو نوع التربة في أرضك؟', '9. Soil Type']);
					let ok = false; for (const val of filters.soilType) { if (matchesGroupedValue(id, '_4', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.climateObserved) {
					const v = getProp(['_5', 'ملاحظة تغيرات مناخية','ملاحظة تغيرات مناخية على الزراعة']);
					const yes = /نعم|yes/i.test(v);
					if (filters.climateObserved === 'yes' && !yes) return false;
					if (filters.climateObserved === 'no' && yes) return false;
				}
			}
			if (id === 'regen-points') {
				if (filters.fertilRel && filters.fertilRel.size) {
					const v = getProp(['_5', 'الاعتماد على الاسمدة الكيميائية']);
					let ok = false; for (const val of filters.fertilRel) { if (matchesGroupedValue(id, '_5', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.pestMgmt && filters.pestMgmt.size) {
					const v = getProp(['_6', 'مكافحة الآفات']);
					let ok = false; for (const val of filters.pestMgmt) { if (matchesGroupedValue(id, '_6', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.regenTech && filters.regenTech.size) {
					const v = getProp(['_3', 'تقنيات الزراعة التجديدية']);
					let ok = false; for (const val of filters.regenTech) { if (matchesGroupedValue(id, '_3', v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
			}
			if (id === 'farmers-points') {
				if (filters.farmerVillage && filters.farmerVillage.size) {
					const v = getProp(['4.القرية:', 'القرية']);
					let ok = false;
					for (const val of filters.farmerVillage) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.farmerCrops && filters.farmerCrops.size) {
					const v = getProp(['10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟']);
					let ok = false;
					for (const val of filters.farmerCrops) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.farmerFarmSize && filters.farmerFarmSize.size) {
					const v = getProp(['8.ما هو حجم الحيازة الزراعية الخاصة بك؟']);
					let ok = false;
					for (const val of filters.farmerFarmSize) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.farmerSoilType && filters.farmerSoilType.size) {
					const v = getProp(['9.ما هو نوع التربة في أرضك؟']);
					let ok = false;
					for (const val of filters.farmerSoilType) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.farmerWaterSource && filters.farmerWaterSource.size) {
					const v = getProp(['13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟']);
					let ok = false;
					for (const val of filters.farmerWaterSource) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.farmerEnergySource && filters.farmerEnergySource.size) {
					const v = getProp(['14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟']);
					let ok = false;
					for (const val of filters.farmerEnergySource) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.farmerRegenPractices) {
					const v = getProp(['32.هل تمارس الزراعة التجديدية؟']);
					const practices = /نعم|yes/i.test(v);
					if (filters.farmerRegenPractices === 'yes' && !practices) return false;
					if (filters.farmerRegenPractices === 'no' && practices) return false;
				}
			}
			if (id === 'fire-points') {
				if (filters.daynight && filters.daynight.size) {
					const v = getProp(['Day\\Night','Day/Night','DAYNIGHT']);
					let ok = false; for (const val of filters.daynight) { if (includesArabicInsensitive(v, val)) { ok = true; break; } }
					if (!ok) return false;
				}
				if (filters.dateMin || filters.dateMax) {
					const t = getProp(['ACQ_DATE','acq_date','date']);
					// try parse as M/D/YYYY
					const d = new Date(t);
					if (filters.dateMin && !(d >= new Date(filters.dateMin))) return false;
					if (filters.dateMax && !(d <= new Date(filters.dateMax))) return false;
				}
				if (filters.timeStart || filters.timeEnd) {
					const v = getProp(['acqtime','ACQ_TIME']);
					const toMin = (s)=>{ if(!s) return null; const m=s.match(/^(\d{1,2}):(\d{2})/); if(!m) return null; return parseInt(m[1],10)*60+parseInt(m[2],10); };
					const valMin = toMin(v);
					const a = toMin(filters.timeStart), b = toMin(filters.timeEnd);
					if (a!=null && valMin!=null && valMin < a) return false;
					if (b!=null && valMin!=null && valMin > b) return false;
				}
			}
			return true;
		});
		// Apply staggering to farmers data to prevent overlaps
		if (id === 'farmers-points') {
			filtered = staggerDuplicateCoordinates(filtered);
		}
	try { 
		src.setData({ type: 'FeatureCollection', features: filtered }); 
		updateLayerCount(id, filtered.length);
	} catch {}
}

function buildSelect(name, values, multiple) {
	const sel = document.createElement('select');
	sel.name = name;
	if (multiple) sel.multiple = true;
	const empty = document.createElement('option'); empty.value = ''; empty.textContent = multiple ? '(none)' : '(any)'; sel.appendChild(empty);
	values.slice(0, 100).forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; sel.appendChild(o); });
	return sel;
}

function createControlGroup(id) {
	const container = document.createElement('div');
	container.className = 'filter-group';
	const row = document.createElement('div'); row.className = 'filter-enable-row';
	const enable = document.createElement('input'); enable.type = 'checkbox'; enable.className = 'filter-enable'; enable.dataset.layer = id;
	const label = document.createElement('label'); 
	label.textContent = i18n.strings[i18n.lang].enableFilters; 
	label.style.marginLeft = '6px';
	label.className = 'i18n-enable-filters';
	row.appendChild(enable); row.appendChild(label);
	const controls = document.createElement('div'); controls.className = 'filter-controls'; controls.style.display = 'none';
	container.appendChild(row); container.appendChild(controls);

	enable.addEventListener('change', () => {
		filterEnabledById[id] = !!enable.checked;
		controls.style.display = enable.checked ? '' : 'none';
		applyFiltersForLayer(id);
	});

	return { container, controls, enable };
}

function addTextControl(parent, labelText, onChange) {
		const wrap = document.createElement('div');
		const lab = document.createElement('div'); lab.textContent = labelText; lab.className = 'filter-label';
		const inp = document.createElement('input'); inp.type = 'text'; inp.className = 'filter-input-text';
		wrap.appendChild(lab); wrap.appendChild(inp); parent.appendChild(wrap);
		inp.addEventListener('input', () => onChange(inp.value));
	}

	function addNumberRange(parent, labelText, onChangeMin, onChangeMax, step) {
		const wrap = document.createElement('div');
		const lab = document.createElement('div'); lab.textContent = labelText; lab.className = 'filter-label';
		const row = document.createElement('div'); row.style.display = 'flex'; row.style.gap = '6px';
		const a = document.createElement('input'); a.type = 'number'; if (step!=null) a.step = step;
		const b = document.createElement('input'); b.type = 'number'; if (step!=null) b.step = step;
		row.appendChild(a); row.appendChild(b); wrap.appendChild(lab); wrap.appendChild(row); parent.appendChild(wrap);
		a.addEventListener('input', () => onChangeMin(a.value === '' ? NaN : parseFloat(a.value)));
		b.addEventListener('input', () => onChangeMax(b.value === '' ? NaN : parseFloat(b.value)));
	}

	function addMonthRange(parent, labelText, onChangeMin, onChangeMax) {
		addNumberRange(parent, labelText, onChangeMin, onChangeMax, 1);
	}

	function addDateRange(parent, labelText, onChangeMin, onChangeMax) {
		const wrap = document.createElement('div');
		const lab = document.createElement('div'); lab.textContent = labelText; lab.className = 'filter-label';
		const row = document.createElement('div'); row.style.display = 'flex'; row.style.gap = '6px';
		const a = document.createElement('input'); a.type = 'date';
		const b = document.createElement('input'); b.type = 'date';
		row.appendChild(a); row.appendChild(b); wrap.appendChild(lab); wrap.appendChild(row); parent.appendChild(wrap);
		a.addEventListener('change', () => onChangeMin(a.value || null));
		b.addEventListener('change', () => onChangeMax(b.value || null));
	}

	function addTimeRange(parent, labelText, onChangeStart, onChangeEnd) {
		const wrap = document.createElement('div');
		const lab = document.createElement('div'); lab.textContent = labelText; lab.className = 'filter-label';
		const row = document.createElement('div'); row.style.display = 'flex'; row.style.gap = '6px';
		const a = document.createElement('input'); a.type = 'time';
		const b = document.createElement('input'); b.type = 'time';
		row.appendChild(a); row.appendChild(b); wrap.appendChild(lab); wrap.appendChild(row); parent.appendChild(wrap);
		a.addEventListener('change', () => onChangeStart(a.value || null));
		b.addEventListener('change', () => onChangeEnd(b.value || null));
	}

	function addMultiSelect(parent, labelText, values, onChange) {
		const wrap = document.createElement('div');
		const lab = document.createElement('div'); lab.textContent = labelText; lab.className = 'filter-label';
		const sel = buildSelect('ms', values, true);
		wrap.appendChild(lab); wrap.appendChild(sel); parent.appendChild(wrap);
		sel.addEventListener('change', () => {
			const set = new Set();
			for (const opt of sel.options) if (opt.selected && opt.value) set.add(opt.value);
			onChange(set);
		});
	}

	function addCheckbox(parent, labelText, onChange) {
		const wrap = document.createElement('div');
		const row = document.createElement('label'); row.style.display = 'flex'; row.style.alignItems = 'center'; row.style.gap = '6px';
		const cb = document.createElement('input'); cb.type = 'checkbox';
		const span = document.createElement('span'); span.textContent = labelText;
		row.appendChild(cb); row.appendChild(span); wrap.appendChild(row); parent.appendChild(wrap);
		cb.addEventListener('change', () => onChange(!!cb.checked));
	}

	function setupFilterUIs() {
		const mapping = {
			'water-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'water-points', () => ({}));
				addMultiSelect(controls, 'Village', uniqueValues('water-points', ['القرية', '4.القرية', '4.القرية:', 'Village', '4. Village']), (set)=>{ state.villageNames = set; applyFiltersForLayer('water-points'); });
				addMultiSelect(controls, 'Crop type', uniqueValues('water-points', ['المحصول', '10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟', '10. Main Crops']), (set)=>{ state.cropTypes = set; applyFiltersForLayer('water-points'); });
				addMultiSelect(controls, 'Irrigation source', uniqueValues('water-points', ['_6', 'مصدر مياه الريّ الرئيسي', '13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟', '13. Water Source']), (set)=>{ state.irrigSource = set; applyFiltersForLayer('water-points'); });
				addMultiSelect(controls, 'Water sufficiency', uniqueValues('water-points', ['_7', 'توفر المياه', '16.كيف تقيّم توفر المياه خلال موسم الزراعة؟', '16. Water Availability']), (set)=>{ state.waterSuff = set; applyFiltersForLayer('water-points'); });
				addMonthRange(controls, 'Scarcity month range (1-12)', (v)=>{ state.scarcityMonthMin = v; applyFiltersForLayer('water-points'); }, (v)=>{ state.scarcityMonthMax = v; applyFiltersForLayer('water-points'); });
				addMultiSelect(controls, 'Irrigation frequency', uniqueValues('water-points', ['_5']), (set)=>{ state.irrigFreq = set; applyFiltersForLayer('water-points'); });
			},
			'energy-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'energy-points', () => ({}));
				addMultiSelect(controls, 'Village', uniqueValues('energy-points', ['القرية', '4.القرية', '4.القرية:', 'Village', '4. Village']), (set)=>{ state.villageNames = set; applyFiltersForLayer('energy-points'); });
				addMultiSelect(controls, 'Energy source', uniqueValues('energy-points', ['_3', 'مصدر الطاقة الرئيسي', '14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟', '14. Energy Source']), (set)=>{ state.energySource = set; applyFiltersForLayer('energy-points'); });
				addCheckbox(controls, 'Has solar', (v)=>{ state.hasSolar = v; applyFiltersForLayer('energy-points'); });
				addCheckbox(controls, 'Has diesel/generator', (v)=>{ state.hasDiesel = v; applyFiltersForLayer('energy-points'); });
				addNumberRange(controls, 'Peak energy amount (min/max)', (v)=>{ state.peakMin = v; applyFiltersForLayer('energy-points'); }, (v)=>{ state.peakMax = v; applyFiltersForLayer('energy-points'); });
			},
			'food-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'food-points', () => ({}));
				addMultiSelect(controls, 'Village', uniqueValues('food-points', ['القرية', '4.القرية', '4.القرية:', 'Village', '4. Village']), (set)=>{ state.villageNames = set; applyFiltersForLayer('food-points'); });
				addMultiSelect(controls, 'Production level', uniqueValues('food-points', ['_5']), (set)=>{ state.production = set; applyFiltersForLayer('food-points'); });
				addMultiSelect(controls, 'Traditional products', uniqueValues('food-points', ['_6']), (set)=>{ state.tradProducts = set; applyFiltersForLayer('food-points'); });
				addCheckbox(controls, 'Has animals', (v)=>{ state.hasAnimals = v; applyFiltersForLayer('food-points'); });
				addNumberRange(controls, 'Bird count (min/max)', (v)=>{ state.birdsMin = v; applyFiltersForLayer('food-points'); }, (v)=>{ state.birdsMax = v; applyFiltersForLayer('food-points'); });
				addMultiSelect(controls, 'Main crops', uniqueValues('food-points', ['_3']), (set)=>{ state.mainCrops = set; applyFiltersForLayer('food-points'); });
			},
			'general-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'general-points', () => ({}));
				addMultiSelect(controls, 'Village', uniqueValues('general-points', ['القرية', '4.القرية', '4.القرية:', 'Village', '4. Village']), (set)=>{ state.villageNames = set; applyFiltersForLayer('general-points'); });
				addMultiSelect(controls, 'Farm size', uniqueValues('general-points', ['_3', 'حجم الزراعة', '8.ما هو حجم الحيازة الزراعية الخاصة بك؟', '8. Farm Size']), (set)=>{ state.farmSize = set; applyFiltersForLayer('general-points'); });
				addMultiSelect(controls, 'Soil type', uniqueValues('general-points', ['_4', 'نوع التربة', '9.ما هو نوع التربة في أرضك؟', '9. Soil Type']), (set)=>{ state.soilType = set; applyFiltersForLayer('general-points'); });
				// yes/no
				(function(controls){
					const wrap = document.createElement('div');
					const lab = document.createElement('div'); lab.textContent = 'Climate change observed'; lab.className = 'filter-label';
					const sel = document.createElement('select');
					[['','(any)'],['yes','Yes'],['no','No']].forEach(([v,t])=>{ const o=document.createElement('option'); o.value=v; o.textContent=t; sel.appendChild(o); });
					wrap.appendChild(lab); wrap.appendChild(sel); controls.appendChild(wrap);
					sel.addEventListener('change', ()=>{ state.climateObserved = sel.value || null; applyFiltersForLayer('general-points'); });
				})(controls);
			},
			'regen-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'regen-points', () => ({}));
				addMultiSelect(controls, 'Village', uniqueValues('regen-points', ['القرية', '4.القرية', '4.القرية:', 'Village', '4. Village']), (set)=>{ state.villageNames = set; applyFiltersForLayer('regen-points'); });
				addMultiSelect(controls, 'Fertilizer reliance', uniqueValues('regen-points', ['_5']), (set)=>{ state.fertilRel = set; applyFiltersForLayer('regen-points'); });
				addMultiSelect(controls, 'Pest management', uniqueValues('regen-points', ['_6']), (set)=>{ state.pestMgmt = set; applyFiltersForLayer('regen-points'); });
				addMultiSelect(controls, 'Regenerative techniques', uniqueValues('regen-points', ['_3']), (set)=>{ state.regenTech = set; applyFiltersForLayer('regen-points'); });
			},
			'fire-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'fire-points', () => ({}));
				addDateRange(controls, 'Acquisition date range', (v)=>{ state.dateMin = v; applyFiltersForLayer('fire-points'); }, (v)=>{ state.dateMax = v; applyFiltersForLayer('fire-points'); });
				(function(controls){
					const wrap = document.createElement('div');
					const lab = document.createElement('div'); lab.textContent = 'Day/Night'; lab.className = 'filter-label';
					const sel = document.createElement('select');
					[['','(any)'],['Day','Day'],['Night','Night']].forEach(([v,t])=>{ const o=document.createElement('option'); o.value=v; o.textContent=t; sel.appendChild(o); });
					wrap.appendChild(lab); wrap.appendChild(sel); controls.appendChild(wrap);
					sel.addEventListener('change', ()=>{ const set = new Set(); if (sel.value) set.add(sel.value); state.daynight = set; applyFiltersForLayer('fire-points'); });
				})(controls);
				addTimeRange(controls, 'Time range', (v)=>{ state.timeStart = v; applyFiltersForLayer('fire-points'); }, (v)=>{ state.timeEnd = v; applyFiltersForLayer('fire-points'); });
				addNumberRange(controls, 'Latitude range', (v)=>{ state.latMin = v; applyFiltersForLayer('fire-points'); }, (v)=>{ state.latMax = v; applyFiltersForLayer('fire-points'); });
				addNumberRange(controls, 'Longitude range', (v)=>{ state.lonMin = v; applyFiltersForLayer('fire-points'); }, (v)=>{ state.lonMax = v; applyFiltersForLayer('fire-points'); });
			},
			'preservations-poly': (controls) => {
				const state = getOrInit(activeFiltersById, 'preservations-poly', () => ({}));
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.nameContains || 'Protected area name', uniqueValues('preservations-poly', ['NAME']), (set)=>{ state.areaNames = set; applyFiltersForLayer('preservations-poly'); });
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.typeCategory || 'Type/Category', uniqueValues('preservations-poly', ['DESIG','DESIG_TYPE','GOV_TYPE']), (set)=>{ state.typeCat = set; applyFiltersForLayer('preservations-poly'); });
				addNumberRange(controls, i18n.strings[i18n.lang].filterLabels.areaRange || 'Area (min/max)', (v)=>{ state.areaMin = v; applyFiltersForLayer('preservations-poly'); }, (v)=>{ state.areaMax = v; applyFiltersForLayer('preservations-poly'); });
			},
			'farmers-points': (controls) => {
				const state = getOrInit(activeFiltersById, 'farmers-points', () => ({}));
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.farmerVillage || 'Village', uniqueValues('farmers-points', ['4.القرية:']), (set)=>{ state.farmerVillage = set; applyFiltersForLayer('farmers-points'); });
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.farmerCrops || 'Main Crops', uniqueValues('farmers-points', ['10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟']), (set)=>{ state.farmerCrops = set; applyFiltersForLayer('farmers-points'); });
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.farmerFarmSize || 'Farm Size', uniqueValues('farmers-points', ['8.ما هو حجم الحيازة الزراعية الخاصة بك؟']), (set)=>{ state.farmerFarmSize = set; applyFiltersForLayer('farmers-points'); });
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.farmerSoilType || 'Soil Type', uniqueValues('farmers-points', ['9.ما هو نوع التربة في أرضك؟']), (set)=>{ state.farmerSoilType = set; applyFiltersForLayer('farmers-points'); });
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.farmerWaterSource || 'Water Source', uniqueValues('farmers-points', ['13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟']), (set)=>{ state.farmerWaterSource = set; applyFiltersForLayer('farmers-points'); });
				addMultiSelect(controls, i18n.strings[i18n.lang].filterLabels.farmerEnergySource || 'Energy Source', uniqueValues('farmers-points', ['14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟']), (set)=>{ state.farmerEnergySource = set; applyFiltersForLayer('farmers-points'); });
				// Regenerative practices yes/no
				(function(controls){
					const wrap = document.createElement('div');
					const lab = document.createElement('div'); lab.textContent = i18n.strings[i18n.lang].filterLabels.farmerRegenPractices || 'Regenerative Agriculture'; lab.className = 'filter-label';
					const sel = document.createElement('select');
					[['','(any)'],['yes','Yes'],['no','No']].forEach(([v,t])=>{ const o=document.createElement('option'); o.value=v; o.textContent=t; sel.appendChild(o); });
					wrap.appendChild(lab); wrap.appendChild(sel); controls.appendChild(wrap);
					sel.addEventListener('change', ()=>{ state.farmerRegenPractices = sel.value || null; applyFiltersForLayer('farmers-points'); });
				})(controls);
			}
		};

		const filterableIds = ['water-points','energy-points','food-points','general-points','regen-points','fire-points','preservations-poly','farmers-points'];
		// Insert UI under each corresponding layer label
		filterableIds.forEach((id) => {
			const label = Array.from(document.querySelectorAll('#sidebar label')).find(l => {
				const inp = l.querySelector('input.layer-toggle');
				return inp && (inp.getAttribute('data-layer') === id || (id==='fire-points' && inp.getAttribute('data-layer')==='fire-points-raw'));
			});
			if (!label) return;
			const { container, controls, enable } = createControlGroup(id);
			label.insertAdjacentElement('afterend', container);
			if (typeof mapping[id] === 'function') mapping[id](controls);
			filterUIById[id] = { container, controls, enable };
			// Initial visibility based on parent layer checkbox state
			const parentToggle = label.querySelector('input.layer-toggle');
			updateFilterGroupVisibility(id, parentToggle);
		});
	}

	function rebuildFilterUIs() {
		// Update 'Enable filters' text for all filter groups
		document.querySelectorAll('.i18n-enable-filters').forEach(label => {
			label.textContent = i18n.strings[i18n.lang].enableFilters;
		});
		
		// Clear existing filter UIs
		Object.entries(filterUIById).forEach(([id, ui]) => {
			if (ui.container && ui.container.parentNode) {
				ui.container.parentNode.removeChild(ui.container);
			}
		});
		
		// Reset filterUIById
		Object.keys(filterUIById).forEach(key => delete filterUIById[key]);
		
		// Rebuild all filters with new language
		setupFilterUIs();
	}

	function updateLayerCount(layerId, count) {
		// Find the corresponding checkbox and update count badge
		const checkbox = document.querySelector(`.layer-toggle[data-layer="${layerId}"]`);
		if (!checkbox) return;
		
		const label = checkbox.parentElement;
		if (!label) return;
		
		// Remove existing count badge if present
		const existingBadge = label.querySelector('.layer-count-badge');
		if (existingBadge) existingBadge.remove();
		
		// Add new count badge on separate line
		if (count >= 0) {
			const badge = document.createElement('span');
			badge.className = 'section-badge layer-count-badge';
			badge.textContent = count;
			badge.style.display = 'block';
			badge.style.marginLeft = '24px';
			badge.style.marginTop = '4px';
			badge.style.marginBottom = '4px';
			badge.style.width = 'fit-content';
			label.appendChild(badge);
		}
	}

	function updateFilterGroupVisibility(targetId, parentInputEl) {
		const ui = filterUIById[targetId];
		if (!ui) return;
		const isDisabled = parentInputEl ? parentInputEl.disabled : false;
		const isChecked = parentInputEl ? parentInputEl.checked : false;
		// Show only when parent is checked and not disabled
		ui.container.style.display = (!isDisabled && isChecked) ? '' : 'none';
		if (!isChecked) {
			// Turn off filters and reset source data
			ui.enable.checked = false;
			filterEnabledById[targetId] = false;
			applyFiltersForLayer(targetId);
			ui.controls.style.display = 'none';
		}
	}

	// Refresh details panel with new language (using PropertySchemas)
	function refreshDetailsPanel(featureId, lang) {
		if (!featureId) return;
		
		// Find feature in themes
		const themes = StateStore.getAllThemes();
		let feature = null;
		let themeKey = null;
		
		for (const [key, theme] of Object.entries(themes)) {
			if (!theme.data || !theme.data.features) continue;
			feature = theme.data.features.find(f => f.properties.featureId === featureId);
			if (feature) {
				themeKey = key;
				break;
			}
		}
		
		if (!feature || !themeKey) {
			console.warn(`Feature ${featureId} not found in themes`);
			return;
		}
		
		// Build details using PropertySchemas
		const panelData = PropertySchemas.buildDetailsPanel(feature, themeKey, lang);
		const content = document.getElementById('details-content');
		if (!content) return;
		
		// Get theme heading (matching old format)
		const headingFor = (theme) => ({
			water: lang === 'ar' ? 'المياه' : 'Water',
			energy: lang === 'ar' ? 'الطاقة' : 'Energy',
			food: lang === 'ar' ? 'الغذاء' : 'Food',
			general: lang === 'ar' ? 'معلومات عامة' : 'General',
			generalinfo: lang === 'ar' ? 'معلومات عامة' : 'General',
			regen: lang === 'ar' ? 'الزراعة التجديدية' : 'Regenerative Agriculture',
			regenerativeagriculture: lang === 'ar' ? 'الزراعة التجديدية' : 'Regenerative Agriculture'
		})[theme] || theme;
		
		// Render in TABLE format (matching old data points exactly)
		let html = `<h4 style="margin:10px 0 6px;">${headingFor(themeKey)}</h4>`;
		
		// Build table rows with all properties
		const rows = [];
		
		// Add village first if present
		if (panelData.villageName) {
			const villageLabel = lang === 'ar' ? 'القرية' : 'Village';
			rows.push(`<tr><th>${villageLabel}</th><td>${panelData.villageName}</td></tr>`);
		}
		
		// Add all other properties
		panelData.details.forEach(({ label, value }) => {
			rows.push(`<tr><th>${label}</th><td>${value}</td></tr>`);
		});
		
		html += `<table>${rows.join('')}</table>`;
		
		content.innerHTML = html;
	}

	function bindPopup(id, sourceIdOverride) {
		const sourceId = sourceIdOverride || id;
		// Hover bubble (no text) on symbol layer
		const symbolId = `${id}-symbols`;
		map.on('mousemove', symbolId, (e) => {
			const prev = hoveredByLayer[symbolId];
			if (prev != null) {
				map.setFeatureState({ source: sourceId, id: prev }, { hover: false });
			}
			const f = e.features && e.features[0];
			if (f && f.id != null) {
				hoveredByLayer[symbolId] = f.id;
				map.setFeatureState({ source: sourceId, id: f.id }, { hover: true });
			}
		});
		map.on('mouseleave', symbolId, () => {
			const prev = hoveredByLayer[symbolId];
			if (prev != null) map.setFeatureState({ source: sourceId, id: prev }, { hover: false });
		});

		// Click opens details sidebar (NEW: uses PropertySchemas for bilingual display)
		map.on('click', symbolId, (e) => {
			const f = e.features && e.features[0];
			if (f && f.properties) {
				const featureId = f.properties.featureId;
				if (featureId) {
					// Store selected feature in state
					StateStore.setState({ selectedFeatureId: featureId });
					
					// Refresh details panel with current language
					const currentLang = StateStore.getLanguage();
					refreshDetailsPanel(featureId, currentLang);
					
					// Open details panel
					const panel = document.getElementById('details');
					if (panel) panel.classList.remove('collapsed');
				} else {
					// Fallback for features without featureId (e.g., static layers)
					openDetailsFromEvent(e.lngLat, e.point);
				}
			}
		});
		map.on('mouseenter', symbolId, () => map.getCanvas().style.cursor = 'pointer');
		map.on('mouseleave', symbolId, () => map.getCanvas().style.cursor = '');
	}

	function openDetailsFromEvent(lngLat, point) {
		const panel = document.getElementById('details');
		const content = document.getElementById('details-content');
		if (!panel || !content) return;
		const pointIds = ['water-points','energy-points','food-points','general-points','regen-points','fire-points','farmers-points', 'ai-regen', 'ai-water', 'ai-econ', 'ai-climate'];
		const visibleSymbolLayers = pointIds.map(id => {
			if (id.startsWith('ai-')) return id; // AI layers are circle layers, not symbol layers
			return `${id}-symbols`;
		}).filter(id => map.getLayer(id) && map.getLayoutProperty(id, 'visibility') !== 'none');
		
		const visibleFillLayers = ['preservations-poly-fill'].filter(id => map.getLayer(id) && map.getLayoutProperty(id, 'visibility') !== 'none');
		
		const feats = [
			...map.queryRenderedFeatures(point, { layers: visibleSymbolLayers }),
			...map.queryRenderedFeatures(point, { layers: visibleFillLayers })
		];
		if (!feats || !feats.length) {
			content.innerHTML = '<div style="padding:8px;color:#555;">No data here.</div>';
			panel.classList.remove('collapsed');
			return;
		}
		const fieldMap = {
			'القرية': 'Village',
			'Y': 'Latitude',
			'X': 'Longitude',
			'المحصول': 'Crop(s)',
			'ريّ المحصول': 'Irrigation',
			'ريّ المحصول 1': 'Irrigation 1',
			'ريّ المحصول 2': 'Irrigation 2',
			'مصدر مياه الريّ الرئيسي': 'Main irrigation source',
			'توفر المياه': 'Water sufficiency',
			' أشهر شح المياه': 'Scarcity months',
			// Thematic layers
			'مصدر الطاقة الرئيسي': 'Main Energy Source',
			'حجم الزراعة': 'Farm Size',
			'نوع التربة': 'Soil Type',
			'الاعتماد على الاسمدة الكيميائية': 'Chemical Fertilizer Reliance',
			'مكافحة الآفات': 'Pest Management',
			'الاعتماد على المبيدات الكيميائية': 'Pesticide Reliance',
			'مستوى الانتاج': 'Production Level',
			'المنتجات التقليدية الرئيسية': 'Traditional Products',
			'المحصولين الرئيسيين': 'Main Crops',
			'theme': 'Theme',
			'source_file': 'Source file',
			'source_row': 'Source row',
			// Farmer survey fields
			'Farmer ID ': 'Farmer ID',
			'1.اسم المُستجيب:': 'Farmer Name',
			'4.القرية:': 'Village',
			'8.ما هو حجم الحيازة الزراعية الخاصة بك؟': 'Farm Size',
			'9.ما هو نوع التربة في أرضك؟': 'Soil Type',
			'10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟': 'Main Crops',
			'13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟': 'Water Source',
			'14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟': 'Energy Source',
			'16.كيف تقيّم توفر المياه خلال موسم الزراعة؟': 'Water Availability',
			'29.ما مدى معرفتك بمفهوم الزراعة التجديدية؟': 'Regenerative Ag Knowledge',
			'32.هل تمارس الزراعة التجديدية؟': 'Practices Regenerative Ag',
			'33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟': 'Regenerative Techniques',
			'38.ما هي أنواع المحسنات التي تستخدمها في التربة؟': 'Soil Amendments',
			'39.ما مدى اعتمادك على الأسمدة الكيميائية؟': 'Chemical Fertilizer Reliance',
			'43.كيف تقوم بمكافحة الآفات؟': 'Pest Management',
			'Pred_Regen_Adoption': 'Predicted Regen Adoption (1=Yes)',
			'Pred_Water_Risk': 'Predicted Water Risk (1=High)',
			'Pred_Production_Level': 'Predicted Production Level (0=Low, 1=Med, 2=High)'
		};
		const prettyKey = (k) => fieldMap[k] || k;
		const cleanValue = (v) => {
			if (v == null) return '';
			const s = String(v).trim();
			const idx = s.indexOf(':');
			if (idx >= 0 && idx < s.length - 1) return s.slice(idx + 1).trim();
			return s;
		};
		const byLayer = {};
		for (const f of feats) {
			let src = f.layer && f.layer.source;
			if (!src) continue;
			// Override source key for AI layers to ensure correct heading
			if (f.layer.id && f.layer.id.startsWith('ai-')) {
				src = f.layer.id.replace('-symbols', '').replace('-bubble', '');
			}
			(byLayer[src] = byLayer[src] || []).push(f);
		}
		const headingFor = (src) => ({
			'water-points': 'Water',
			'energy-points': 'Energy',
			'food-points': 'Food',
			'general-points': 'General',
			'regen-points': 'Regenerative Agriculture',
			'fire-points': 'Fire points',
			'preservations-poly': 'Preservations',
			'farmers-points': 'Farmer Survey',
			'ai-regen': 'AI: Regenerative Adoption',
			'ai-water': 'AI: Water Risk',
			'ai-econ': 'AI: Economic Resilience',
			'ai-labor': 'AI: Labor Availability',
			'ai-climate': 'AI: Climate Vulnerability'
		})[src] || src;
		// Overlap disambiguation for polygons
		const sections = Object.keys(byLayer).map(src => {
			const features = byLayer[src];
			if (src === 'preservations-poly' && features.length > 1) {
				const items = features.map((f, idx) => {
					const p = f.properties || {};
					const title = p.NAME || p.ORIG_NAME || `Area ${idx+1}`;
					return `<li data-fid="${f.id}">${title}</li>`;
				}).join('');
				const details = (f) => {
					const p = f.properties || {};
					const tr = Object.keys(p).sort().map(k => `<tr><th>${prettyKey(k)}</th><td>${cleanValue(p[k])}</td></tr>`).join('');
					return `<table>${tr}</table>`;
				};
				// default to smallest area if available (using bbox width*height as proxy)
				const sorted = features.slice().sort((a,b)=>{
					const ab = a.bbox || [];
					const bb = b.bbox || [];
					const aw = (ab[2]-ab[0]) * (ab[3]-ab[1]) || 0;
					const bw = (bb[2]-bb[0]) * (bb[3]-bb[1]) || 0;
					return aw - bw;
				});
				const initial = sorted[0];
				setTimeout(()=>{
					const ul = document.getElementById('overlap-list');
					if (!ul) return;
					ul.querySelectorAll('li').forEach(li => {
						li.addEventListener('mouseenter', ()=>{
							const fid = li.getAttribute('data-fid');
							if (fid) map.setFeatureState({ source: 'preservations-poly', id: parseInt(fid,10) }, { hover: true });
						});
						li.addEventListener('mouseleave', ()=>{
							const fid = li.getAttribute('data-fid');
							if (fid) map.setFeatureState({ source: 'preservations-poly', id: parseInt(fid,10) }, { hover: false });
						});
						li.addEventListener('click', ()=>{
							const fid = li.getAttribute('data-fid');
							const f = features.find(x=> String(x.id) === String(fid));
							const panel = document.getElementById('details-content');
							if (panel && f) panel.innerHTML = `<h4 style=\"margin:10px 0 6px;\">${headingFor('preservations-poly')}</h4>` + details(f);
						});
					});
				}, 0);
				return `<h4 style=\"margin:10px 0 6px;\">${headingFor(src)}</h4><div><div style=\"margin-bottom:6px;\">Multiple areas here, hover to highlight and click to select:</div><ul id=\"overlap-list\" style=\"padding-left:18px;\">${items}</ul>${details(initial)}</div>`;
			}
			// default rendering
			const rows = features.map(f => {
				const p = f.properties || {};
				// For farmers-points, show only key fields
				if (src === 'farmers-points') {
					const keyFields = [
						'Farmer ID ',
						'1.اسم المُستجيب:',
						'4.القرية:',
						'Y',
						'X',
						'8.ما هو حجم الحيازة الزراعية الخاصة بك؟',
						'9.ما هو نوع التربة في أرضك؟',
						'10.ما هما المحصولان الرئيسيان اللذان تزرعهما خلال السنة (حسب المساحة أو الدخل)؟',
						'13.ما هو المصدر الرئيسي للمياه المستخدمة في الري؟',
						'14.ما هو مصدر الطاقة الرئيسي الذي تستخدمه للري والعمليات الزراعية؟',
						'16.كيف تقيّم توفر المياه خلال موسم الزراعة؟',
						'32.هل تمارس الزراعة التجديدية؟',
						'33.ما هي التقنيات التي تطبقها من الزراعة التجديدية؟'
					];
					const tr = keyFields.filter(k => p[k]).map(k => `<tr><th>${prettyKey(k)}</th><td>${cleanValue(p[k])}</td></tr>`).join('');
					return `<table>${tr}</table>`;
				}
				// For other sources, show all fields
				const tr = Object.keys(p).sort().map(k => `<tr><th>${prettyKey(k)}</th><td>${cleanValue(p[k])}</td></tr>`).join('');
				return `<table>${tr}</table>`;
			}).join('<hr>');
			return `<h4 style=\"margin:10px 0 6px;\">${headingFor(src)}</h4>${rows}`;
		}).join('');
		content.innerHTML = sections || '<div style="padding:8px;color:#555;">No data.</div>';
		panel.classList.remove('collapsed');
	}

	(function setupDetailsClose(){
		const btn = document.getElementById('details-close');
		if (btn) btn.addEventListener('click', () => {
			const panel = document.getElementById('details');
			if (panel) panel.classList.add('collapsed');
		});
	})();

	function bindClusterInteraction(id) {
		const clustersId = `${id}-clusters`;
		map.on('click', clustersId, (e) => {
			const features = map.queryRenderedFeatures(e.point, { layers: [clustersId] });
			if (!features || !features.length) return;
			const f = features[0];
			const clusterId = f.properties && f.properties.cluster_id;
			const src = map.getSource(id);
			if (!src || clusterId == null) return;
			src.getClusterExpansionZoom(clusterId, (err, zoom) => {
				if (err) return;
				map.easeTo({ center: f.geometry.coordinates, zoom });
			});
		});
		map.on('mouseenter', clustersId, () => map.getCanvas().style.cursor = 'pointer');
		map.on('mouseleave', clustersId, () => map.getCanvas().style.cursor = '');
	}

	map.on('load', () => {
		// Sync language on startup
		const savedLang = localStorage.getItem('uiLang') || 'en';
		i18n.lang = savedLang;
		StateStore.setLanguage(savedLang);
		i18n.apply(); // Apply language to UI immediately
		
		setupSidebarCollapse();
		installSidebarIcons();
		setupBaseMapRadios();
		setupToggles();
		loadAllData();
		
		// language toggle (NEW: No data reloading, presentation only)
		(function setupLangToggle(){
			const btn = document.getElementById('lang-toggle');
			if (!btn) return;
			btn.addEventListener('click', () => {
				const currentLang = i18n.lang;
				const newLang = currentLang === 'ar' ? 'en' : 'ar';
				
				// Update i18n for UI labels (also updates localStorage)
				i18n.setLang(newLang);
				
				// Update state
				StateStore.setLanguage(newLang);
				
				// Refresh details panel if open (using new schema)
				const selectedId = StateStore.getState().selectedFeatureId;
				if (selectedId) {
					refreshDetailsPanel(selectedId, newLang);
				}
				
				// Rebuild filter UIs with new language options
				rebuildFilterUIs();
				
				console.log(`✓ Language switched to ${newLang} (no data reload)`);
			});
			i18n.apply();
		})();


		// Install one-time dynamic cluster icon generator (avoids glyph/font dependency)
		if (!clusterIconHandlerInstalled) {
			map.on('styleimagemissing', (e) => {
				const id = e && e.id;
				if (!id || !id.startsWith('cluster-')) return;
			  
				const parts = id.split('-');
				if (parts.length < 3) return;
			  
				const key = parts[1];
				const countStr = parts.slice(2).join('-');
				const color = clusterColors[key] || '#555';
			  
				const dpr = 2;           // HiDPI ratio
				const size = 40;         // logical px (larger base to avoid clipping)
				const canvas = document.createElement('canvas');
				canvas.width  = size * dpr;
				canvas.height = size * dpr;
			  
				const ctx = canvas.getContext('2d');
				ctx.scale(dpr, dpr);
			  
				// Circle
				const r = (size / 2) - 3;
				ctx.beginPath();
				ctx.arc(size / 2, size / 2, r, 0, Math.PI * 2);
				ctx.fillStyle = color;
				ctx.globalAlpha = 0.9;
				ctx.fill();
				ctx.globalAlpha = 1;
				ctx.lineWidth = 2.5;
				ctx.strokeStyle = '#fff';
				ctx.stroke();
			  
				// Count text (scale with digits)
				const digits = countStr.length;
				const fontPx = Math.round(
				  digits <= 2 ? size * 0.55 :
				  digits === 3 ? size * 0.48 :
								 size * 0.42
				);
				ctx.font = `600 ${fontPx}px system-ui, -apple-system, Segoe UI, Roboto, Arial`;
				ctx.textAlign = 'center';
				ctx.textBaseline = 'middle';
				ctx.fillStyle = '#fff';
			  
				// Optional thin halo to keep text readable on bright fills
				ctx.lineWidth = Math.max(1, Math.round(size * 0.04));
				ctx.strokeStyle = 'rgba(0,0,0,0.25)';
				ctx.strokeText(countStr, size / 2, size / 2 + size * 0.01);
				ctx.fillText(countStr,   size / 2, size / 2 + size * 0.01);
			  
				// IMPORTANT: pass full canvas area to ImageData and the same pixelRatio
				const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
				map.addImage(id, img, { pixelRatio: dpr });
			  });
			  
			clusterIconHandlerInstalled = true;
		}
	});

	function setupBaseMapRadios() {
		document.querySelectorAll('.basemap-radio').forEach(r => {
			r.addEventListener('change', () => {
				const val = r.value;
				const all = ['osm','esri','carto-light','carto-dark','opentopo'];
				all.forEach(id => { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', id === val ? 'visible' : 'none'); });
				keepBasemapsAtBottom();
			});
		});

		// Initialize extra sources/layers once
		map.once('load', () => {
			const ensureRaster = (srcId, tiles, attribution) => {
				if (!map.getSource(srcId)) map.addSource(srcId, { type: 'raster', tiles, tileSize: 256, attribution });
				if (!map.getLayer(srcId)) map.addLayer({ id: srcId, type: 'raster', source: srcId, layout: { visibility: 'none' } });
			};
			ensureRaster('carto-light', ['https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'], '© CARTO');
			ensureRaster('carto-dark', ['https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'], '© CARTO');
			ensureRaster('opentopo', ['https://tile.opentopomap.org/{z}/{x}/{y}.png'], '© OpenTopoMap');

			keepBasemapsAtBottom();
		});

	}

	function keepBasemapsAtBottom() {
		const baseIds = ['osm','esri','carto-light','carto-dark','opentopo'];
		const layers = (map.getStyle() && map.getStyle().layers) ? map.getStyle().layers.slice() : [];
		
		if (!layers.length) return;
		
		// Create set for easier lookup
		const basemapSet = new Set(baseIds.filter(id => map.getLayer(id)));
		
		// Find the topmost basemap layer to use as reference
		let topBasemap = null;
		for (const id of baseIds) {
			if (map.getLayer(id)) topBasemap = id;
		}
		
		if (!topBasemap) return;
		
		// Ensure all data layers are above basemaps
		const dataLayerPatterns = [
			// Point layer patterns (bubbles should be below symbols)
			'-bubble',
			'-symbols', 
			'-clusters',
			'-cluster-count',
			// Polygon patterns
			'-fill',
			'-outline',
			// Special layers
			'fire-heatmap'
		];
		
		// Get all data layers that should be on top
		const dataLayers = layers.filter(layer => {
			const layerId = layer.id;
			// Skip basemaps
			if (basemapSet.has(layerId)) return false;
			// Include layers matching our data patterns or other non-basemap layers
			return dataLayerPatterns.some(pattern => layerId.includes(pattern)) || 
				   (!layerId.includes('osm') && !layerId.includes('esri') && !layerId.includes('carto') && !layerId.includes('opentopo'));
		});
		
		// Sort data layers to maintain proper stacking (bubbles before symbols, etc.)
		dataLayers.sort((a, b) => {
			const aId = a.id;
			const bId = b.id;
			
			// Bubbles should come before symbols for the same base layer
			if (aId.includes('-bubble') && bId.includes('-symbols') && 
				aId.replace('-bubble', '') === bId.replace('-symbols', '')) {
				return -1;
			}
			if (bId.includes('-bubble') && aId.includes('-symbols') && 
				bId.replace('-bubble', '') === aId.replace('-symbols', '')) {
				return 1;
			}
			
			// Fill should come before outline for polygons
			if (aId.includes('-fill') && bId.includes('-outline') && 
				aId.replace('-fill', '') === bId.replace('-outline', '')) {
				return -1;
			}
			if (bId.includes('-fill') && aId.includes('-outline') && 
				bId.replace('-fill', '') === aId.replace('-outline', '')) {
				return 1;
			}
			
			return 0;
		});
		
		// Move data layers above basemaps, maintaining their internal order
		for (const layer of dataLayers) {
			try {
				map.moveLayer(layer.id);  // Move to top
			} catch (e) {
				console.warn(`Failed to move layer ${layer.id}:`, e);
			}
		}
		
		// Debug: Log current layer order (only in development)
		if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
			const currentLayers = map.getStyle().layers.map(l => l.id);
			console.log('🔄 Layer order after keepBasemapsAtBottom:', currentLayers);
		}
	}

	function addBoundaryLayer() {
		const id = 'farmers-boundary';
		const url = fromRoot('data/geojson/Farmers_Boundary.geojson');
		if (map.getSource(id)) return;
		map.addSource(id, { type: 'geojson', data: url });
		map.addLayer({
			id: id,
			type: 'line',
			source: id,
			layout: { visibility: 'none' },
			paint: {
				'line-color': '#2c3e50',
				'line-width': 2,
				'line-dasharray': [2, 2],
				'line-opacity': 0.7
			}
		});
		// Optional fill
		map.addLayer({
			id: `${id}-fill`,
			type: 'fill',
			source: id,
			layout: { visibility: 'none' },
			paint: {
				'fill-color': '#2c3e50',
				'fill-opacity': 0.05
			}
		}, id); // Place fill below line
	}

	/**
	 * Add AI Prediction Layer (Updated for discrete classifications)
	 * Uses categorical coloring instead of probability gradients
	 * Data: Model_Predictions.geojson with 204 scenarios
	 * Predictions: "0", "1", "2" (discrete, not continuous)
	 */
	function addAiHeatmapLayer(id, type) {
		const sourceId = 'ai-predictions';
		const url = fromRoot('data/geojson/Model_Predictions.geojson');
		
		// Shared source for all AI layers (loaded once)
		if (!map.getSource(sourceId)) {
			map.addSource(sourceId, { 
				type: 'geojson', 
				data: url,
				promoteId: 'source_row'  // Use source_row as stable ID for feature-state
			});
		}
		
		let predProp;    // Prediction property name
		let colorMap;    // Categorical color mapping
		let description; // Layer description for legend
		
		if (type === 'regen') {
			predProp = 'Pred_Regen_Adoption';
			description = 'Regenerative Agriculture Adoption';
			// Binary: 0 = No adoption (red), 1 = Adoption (green)
			colorMap = [
				'match',
				['get', predProp],
				'0', '#e74c3c',  // Red - No adoption
				'1', '#27ae60',  // Green - Adoption
				'#95a5a6'        // Gray - Unknown/missing
			];
		} else if (type === 'water') {
			predProp = 'Pred_Water_Risk';
			description = 'Water Scarcity Risk';
			// Binary: 0 = Low risk (green), 1 = High risk (red) - inverted logic
			colorMap = [
				'match',
				['get', predProp],
				'0', '#27ae60',  // Green - Low risk
				'1', '#e74c3c',  // Red - High risk
				'#95a5a6'        // Gray - Unknown
			];
		} else if (type === 'econ') {
			predProp = 'Pred_Production_Level';
			description = 'Production Capacity';
			// Ternary: 0 = Low (red), 1 = Medium (yellow), 2 = High (green)
			colorMap = [
				'match',
				['get', predProp],
				'0', '#e74c3c',  // Red - Low production
				'1', '#f39c12',  // Yellow - Medium production
				'2', '#27ae60',  // Green - High production
				'#95a5a6'        // Gray - Unknown
			];
		} else if (type === 'climate') {
			// Placeholder for future climate vulnerability predictions
			// Currently using production level as proxy
			predProp = 'Pred_Production_Level';
			description = 'Climate Resilience Proxy';
			colorMap = [
				'match',
				['get', predProp],
				'0', '#3498db',  // Blue - Low resilience
				'1', '#9b59b6',  // Purple - Medium resilience
				'2', '#1abc9c',  // Teal - High resilience
				'#95a5a6'        // Gray - Unknown
			];
		}

		// Add circle layer with categorical coloring and improved transparency
		if (!map.getLayer(id)) {
			map.addLayer({
				id: id,
				type: 'circle',
				source: sourceId,
				layout: { visibility: 'none' },
				paint: {
					// Larger circles for better visibility of discrete categories
					'circle-radius': [
						'interpolate', ['linear'], ['zoom'],
						8, 6,   // Small at low zoom
						10, 8,
						12, 10,
						14, 12,
						16, 14
					],
					// Categorical color based on prediction value
					'circle-color': colorMap,
					// Improved transparency for map clarity (user requirement)
					'circle-opacity': [
						'case',
						['boolean', ['feature-state', 'hover'], false],
						0.95,  // Full opacity on hover
						0.7    // 70% opacity normally for "more transparent" map
					],
					// White stroke for definition
					'circle-stroke-width': [
						'case',
						['boolean', ['feature-state', 'hover'], false],
						2,     // Thicker on hover
						1      // Normal stroke
					],
					'circle-stroke-color': '#ffffff',
					'circle-stroke-opacity': 0.9
				}
			});
			
			// Store description for legend
			map.setLayerMetadata = map.setLayerMetadata || {};
			map.setLayerMetadata[id] = { description, predProp, type };
		}
	}

	function updateAiBoundaryVisibility() {
		const aiLayers = ['ai-regen', 'ai-water', 'ai-econ', 'ai-climate'];
		const anyActive = aiLayers.some(id => map.getLayer(id) && map.getLayoutProperty(id, 'visibility') === 'visible');
		const boundaryId = 'farmers-boundary';
		const vis = anyActive ? 'visible' : 'none';
		
		if (map.getLayer(boundaryId)) map.setLayoutProperty(boundaryId, 'visibility', vis);
		if (map.getLayer(`${boundaryId}-fill`)) map.setLayoutProperty(`${boundaryId}-fill`, 'visibility', vis);
		
		updateLegend(anyActive);
	}

	function updateLegend(show) {
		let legend = document.getElementById('ai-legend');
		if (!show) {
			if (legend) legend.style.display = 'none';
			return;
		}
		if (!legend) {
			legend = document.createElement('div');
			legend.id = 'ai-legend';
			legend.className = 'map-legend';
			document.body.appendChild(legend);
			
			// Add styles dynamically if not present
			if (!document.getElementById('legend-style')) {
				const style = document.createElement('style');
				style.id = 'legend-style';
				style.textContent = `
					.map-legend {
						position: absolute; bottom: 30px; right: 10px;
						background: rgba(255,255,255,0.95); padding: 12px;
						border-radius: 6px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);
						font-family: sans-serif; font-size: 12px;
						z-index: 10; max-width: 220px;
					}
					.legend-item { margin-bottom: 12px; }
					.legend-title { 
						font-weight: bold; 
						margin-bottom: 6px; 
						display: block; 
						font-size: 13px;
						color: #333;
					}
					.legend-category {
						display: flex;
						align-items: center;
						margin: 4px 0;
					}
					.legend-dot {
						width: 14px;
						height: 14px;
						border-radius: 50%;
						border: 2px solid #fff;
						margin-right: 8px;
						box-shadow: 0 1px 3px rgba(0,0,0,0.2);
					}
					.legend-label {
						color: #555;
						font-size: 11px;
					}
				`;
				document.head.appendChild(style);
			}
		}
		
		legend.style.display = 'block';
		let html = '';
		
		// Regenerative Adoption - Binary classification
		if (map.getLayoutProperty('ai-regen', 'visibility') === 'visible') {
			html += `
				<div class="legend-item">
					<span class="legend-title">Regenerative Adoption</span>
					<div class="legend-category">
						<span class="legend-dot" style="background:#e74c3c"></span>
						<span class="legend-label">Unlikely to Adopt</span>
					</div>
					<div class="legend-category">
						<span class="legend-dot" style="background:#27ae60"></span>
						<span class="legend-label">Likely to Adopt</span>
					</div>
				</div>`;
		}
		
		// Water Risk - Binary classification (inverted logic)
		if (map.getLayoutProperty('ai-water', 'visibility') === 'visible') {
			html += `
				<div class="legend-item">
					<span class="legend-title">Water Risk</span>
					<div class="legend-category">
						<span class="legend-dot" style="background:#27ae60"></span>
						<span class="legend-label">Low Risk</span>
					</div>
					<div class="legend-category">
						<span class="legend-dot" style="background:#e74c3c"></span>
						<span class="legend-label">High Risk</span>
					</div>
				</div>`;
		}
		
		// Production Level - Ternary classification
		if (map.getLayoutProperty('ai-econ', 'visibility') === 'visible') {
			html += `
				<div class="legend-item">
					<span class="legend-title">Production Capacity</span>
					<div class="legend-category">
						<span class="legend-dot" style="background:#e74c3c"></span>
						<span class="legend-label">Low Production</span>
					</div>
					<div class="legend-category">
						<span class="legend-dot" style="background:#f39c12"></span>
						<span class="legend-label">Medium Production</span>
					</div>
					<div class="legend-category">
						<span class="legend-dot" style="background:#27ae60"></span>
						<span class="legend-label">High Production</span>
					</div>
				</div>`;
		}
		
		// Climate layer (using production as proxy)
		if (map.getLayoutProperty('ai-climate', 'visibility') === 'visible') {
			html += `
				<div class="legend-item">
					<span class="legend-title">Climate Resilience</span>
					<div class="legend-category">
						<span class="legend-dot" style="background:#3498db"></span>
						<span class="legend-label">Low Resilience</span>
					</div>
					<div class="legend-category">
						<span class="legend-dot" style="background:#9b59b6"></span>
						<span class="legend-label">Medium Resilience</span>
					</div>
					<div class="legend-category">
						<span class="legend-dot" style="background:#1abc9c"></span>
						<span class="legend-label">High Resilience</span>
					</div>
				</div>`;
		}
		
		legend.innerHTML = html || '<div style="color:#666; padding:8px;">Select an AI layer to see legend</div>';
	}

	// Load all thematic layers using new canonical architecture
	async function loadAllData() {
		// Initialize state management
		StateStore.restoreState();
		
		// Initialize IndexedDB data loader
		await DataLoader.init();
		
		// Load canonical bilingual theme data with progress
		console.log('Loading canonical bilingual data...');
		const themes = await DataLoader.loadAllThemes((loaded, total, key) => {
			console.log(`✓ Loaded ${loaded}/${total}: ${key}`);
		});
		
		// Store themes in state
		StateStore.setState({ themes, themesLoaded: true });
		
		// Add canonical layers to map
		addCanonicalLayer('water-points', themes.water);
		addCanonicalLayer('energy-points', themes.energy);
		addCanonicalLayer('food-points', themes.food);
		addCanonicalLayer('general-points', themes.general);
		addCanonicalLayer('regen-points', themes.regen);
		
		// Load static layers (fire, preservations, predictions)
		const staticLayers = await DataLoader.loadStaticLayers();
		StateStore.setState({ staticLayers });
		
		// Fire: add raw (for heatmap) and clustered copy for symbols
		if (staticLayers.fire) {
			addGeoJsonLayer('fire-points-raw', staticLayers.fire, '#e74c3c', false);
			addGeoJsonLayer('fire-points', staticLayers.fire, '#e74c3c', true);
			updateLayerCount('fire-points', staticLayers.fire.features.length);
		}
		// Farmers comprehensive survey (using Model_Predictions to include AI data)
		if (staticLayers.predictions) {
			addGeoJsonLayer('farmers-points', staticLayers.predictions, '#16a085', true);
			updateLayerCount('farmers-points', staticLayers.predictions.features.length);
		}
		// Preservations polygons
		if (staticLayers.preservations) {
			addPolygonLayer('preservations-poly', staticLayers.preservations, '#2ecc71');
			updateLayerCount('preservations-poly', staticLayers.preservations.features.length);
		}
		
		// Boundary Layer
		addBoundaryLayer();

		// AI Layers (Heatmaps)
		addAiHeatmapLayer('ai-regen', 'regen');
		addAiHeatmapLayer('ai-water', 'water');
		addAiHeatmapLayer('ai-econ', 'econ');
		// Skip labor layer - insufficient training data (only 4 positive samples)
		// addAiHeatmapLayer('ai-labor', 'labor');
		addAiHeatmapLayer('ai-climate', 'climate');

		// Preload originals for filtering and unique value extraction
		await Promise.all([
			preloadGeoJson('water-points'),
			preloadGeoJson('energy-points'),
			preloadGeoJson('food-points'),
			preloadGeoJson('general-points'),
			preloadGeoJson('regen-points'),
			preloadGeoJson('fire-points'),
			preloadGeoJson('farmers-points')
		]);

		['water-points','energy-points','food-points','general-points','regen-points','fire-points','farmers-points'].forEach(id => bindPopup(id));
		['water-points','energy-points','food-points','general-points','regen-points','fire-points','farmers-points'].forEach(bindClusterInteraction);
		bindPolygonInteraction('preservations-poly');

		// enable toggles
		document.querySelectorAll('.layer-toggle, #toggle-heatmap').forEach(el => {
			el.disabled = false;
			if (el.classList.contains('layer-toggle')) {
				let layerId = el.getAttribute('data-layer');
				// Fire special-case: toggle clustered visual for 'fire-points'
				let targetId = (layerId === 'fire-points-raw') ? 'fire-points' : layerId;
				const visible = el.checked ? 'visible' : 'none';
				
				// AI Layers special case
				if (layerId.startsWith('ai-')) {
					if (map.getLayer(layerId)) map.setLayoutProperty(layerId, 'visibility', visible);
					updateAiBoundaryVisibility();
					keepBasemapsAtBottom();
					return;
				}

				// points handling
				if (map.getLayer(targetId)) map.setLayoutProperty(targetId, 'visibility', visible);
				const symbolId = `${targetId}-symbols`;
				const bubbleId = `${targetId}-bubble`;
				if (map.getLayer(symbolId)) map.setLayoutProperty(symbolId, 'visibility', visible);
				if (map.getLayer(bubbleId)) map.setLayoutProperty(bubbleId, 'visibility', visible);
				const clustersId = `${targetId}-clusters`;
				const clusterCountId = `${targetId}-cluster-count`;
				if (map.getLayer(clustersId)) map.setLayoutProperty(clustersId, 'visibility', visible);
				if (map.getLayer(clusterCountId)) map.setLayoutProperty(clusterCountId, 'visibility', visible);
				// polygons handling
				const fillId = `${targetId}-fill`;
				const outlineId = `${targetId}-outline`;
				if (map.getLayer(fillId)) map.setLayoutProperty(fillId, 'visibility', visible);
				if (map.getLayer(outlineId)) map.setLayoutProperty(outlineId, 'visibility', visible);
			}
		});

		// Native heatmap for fire points
		setupFireHeatmapLayer();
		
		// Ensure all data layers are properly stacked
		setTimeout(() => {
			keepBasemapsAtBottom();
		}, 100);

		// Build filter UIs after data is available
		setupFilterUIs();
	}

	function setupLoadButton() {
		// deprecated: auto load happens on map load
	}

	function setupToggles() {
		document.querySelectorAll('.layer-toggle').forEach(input => {
			input.addEventListener('change', (ev) => {
				let layerId = ev.target.getAttribute('data-layer');
				const visible = ev.target.checked ? 'visible' : 'none';
				
				// AI Layers special case
				if (layerId.startsWith('ai-')) {
					if (map.getLayer(layerId)) map.setLayoutProperty(layerId, 'visibility', visible);
					updateAiBoundaryVisibility();
					keepBasemapsAtBottom();
					return;
				}

				// Fire special-case uses clustered 'fire-points' for visuals
				let targetId = (layerId === 'fire-points-raw') ? 'fire-points' : layerId;
				if (map.getLayer(targetId)) map.setLayoutProperty(targetId, 'visibility', visible);
				const symbolId = `${targetId}-symbols`;
				const bubbleId = `${targetId}-bubble`;
				if (map.getLayer(symbolId)) map.setLayoutProperty(symbolId, 'visibility', visible);
				if (map.getLayer(bubbleId)) map.setLayoutProperty(bubbleId, 'visibility', visible);
				const clustersId = `${targetId}-clusters`;
				const clusterCountId = `${targetId}-cluster-count`;
				if (map.getLayer(clustersId)) map.setLayoutProperty(clustersId, 'visibility', visible);
				if (map.getLayer(clusterCountId)) map.setLayoutProperty(clusterCountId, 'visibility', visible);
				const fillId = `${targetId}-fill`;
				const outlineId = `${targetId}-outline`;
				if (map.getLayer(fillId)) map.setLayoutProperty(fillId, 'visibility', visible);
				if (map.getLayer(outlineId)) map.setLayoutProperty(outlineId, 'visibility', visible);
				// Update filter UI visibility tied to parent toggle
				updateFilterGroupVisibility(targetId, ev.target);
				
				// Ensure proper layer stacking after any layer toggle
				keepBasemapsAtBottom();
			});
		});
	}

// (AI overlays removed)

	// MapLibre native heatmap layer for fire points with better color ramp
	function setupFireHeatmapLayer() {
		if (!map.getSource('fire-points-raw')) return;
		if (!map.getLayer('fire-heatmap')) {
			map.addLayer({
				id: 'fire-heatmap',
				type: 'heatmap',
				source: 'fire-points-raw',
				maxzoom: 15,
				layout: { visibility: 'none' },
				paint: {
					'heatmap-weight': 1,
					'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 6, 0.7, 12, 2.0],
					'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 6, 10, 12, 26],
					'heatmap-color': [
						'interpolate', ['linear'], ['heatmap-density'],
						0.0, 'rgba(0,0,0,0)',
						0.2, '#2c7fb8',
						0.4, '#41b6c4',
						0.6, '#a1dab4',
						0.8, '#ffffbf',
						0.9, '#fdae61',
						1.0, '#d7191c'
					],
					'heatmap-opacity': 0.9
				}
			});
		}
		const toggle = document.getElementById('toggle-heatmap');
		if (toggle) {
			const vis = toggle.checked ? 'visible' : 'none';
			map.setLayoutProperty('fire-heatmap', 'visibility', vis);
			toggle.addEventListener('change', () => {
				map.setLayoutProperty('fire-heatmap', 'visibility', toggle.checked ? 'visible' : 'none');
				keepBasemapsAtBottom();
			});
		}
	}

	// --- NEW UI ENHANCEMENTS ---
	
	// Hide loading overlay once map is loaded
	map.on('load', () => {
		setTimeout(() => {
			const loadingOverlay = document.getElementById('loading-overlay');
			if (loadingOverlay) {
				loadingOverlay.classList.add('hidden');
				setTimeout(() => loadingOverlay.remove(), 500);
			}
		}, 1000);
	});

	// Layer counter badge
	function updateTotalLayerCount() {
		const checkedLayers = document.querySelectorAll('.layer-toggle:checked').length;
		const heatmapChecked = document.getElementById('toggle-heatmap')?.checked ? 1 : 0;
		const total = checkedLayers + heatmapChecked;
		
		const badge = document.getElementById('layer-count');
		if (badge) {
			badge.textContent = total;
			badge.style.opacity = total > 0 ? '1' : '0.5';
		}
	}

	// Update counter when layers toggle
	document.addEventListener('change', (e) => {
		if (e.target.classList.contains('layer-toggle') || e.target.id === 'toggle-heatmap') {
			updateTotalLayerCount();
		}
	});

	// Custom zoom controls
	const zoomInBtn = document.getElementById('zoom-in');
	const zoomOutBtn = document.getElementById('zoom-out');
	const resetViewBtn = document.getElementById('reset-view');

	if (zoomInBtn) {
		zoomInBtn.addEventListener('click', () => {
			map.zoomIn({ duration: 300 });
		});
	}

	if (zoomOutBtn) {
		zoomOutBtn.addEventListener('click', () => {
			map.zoomOut({ duration: 300 });
		});
	}

	if (resetViewBtn) {
		resetViewBtn.addEventListener('click', () => {
			map.flyTo({
				center: [35.6, 33.7],
				zoom: 9,
				duration: 1000
			});
		});
	}

	// Keyboard shortcuts
	document.addEventListener('keydown', (e) => {
		// ESC to close details panel
		if (e.key === 'Escape') {
			const details = document.getElementById('details');
			if (details && !details.classList.contains('collapsed')) {
				details.classList.add('collapsed');
			}
		}
		
		// Ctrl/Cmd + [ to toggle sidebar
		if ((e.ctrlKey || e.metaKey) && e.key === '[') {
			e.preventDefault();
			const sidebar = document.getElementById('sidebar');
			const sidebarToggle = document.getElementById('sidebar-toggle');
			if (sidebar && sidebarToggle) {
				sidebar.classList.toggle('collapsed');
			}
		}
		
		// Ctrl/Cmd + L to toggle language
		if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
			e.preventDefault();
			const langBtn = document.getElementById('lang-toggle');
			if (langBtn) langBtn.click();
		}
	});

	// Initialize layer counter
	updateTotalLayerCount();

	// Add smooth transitions for map interactions
	map.on('movestart', () => {
		document.body.style.cursor = 'grabbing';
	});

	map.on('moveend', () => {
		document.body.style.cursor = '';
	});

	// Show toast notification helper
	function showToast(message, duration = 3000) {
		const toast = document.createElement('div');
		toast.className = 'toast-notification';
		toast.textContent = message;
		toast.style.cssText = `
			position: fixed;
			bottom: 100px;
			left: 50%;
			transform: translateX(-50%) translateY(100px);
			background: rgba(0, 0, 0, 0.85);
			color: white;
			padding: 12px 24px;
			border-radius: 8px;
			font-size: 14px;
			z-index: 10000;
			transition: transform 0.3s ease;
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		`;
		document.body.appendChild(toast);
		
		setTimeout(() => {
			toast.style.transform = 'translateX(-50%) translateY(0)';
		}, 10);
		
		setTimeout(() => {
			toast.style.transform = 'translateX(-50%) translateY(100px)';
			setTimeout(() => toast.remove(), 300);
		}, duration);
	}

	// Expose toast for other parts of the app
	window.showToast = showToast;
})();



