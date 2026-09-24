/**
 * Hindi copy.
 *
 * NOT YET REVIEWED BY A NATIVE SPEAKER. See LOCALE_META in ../locales.ts and
 * the translation section of CONTRIBUTING.md.
 *
 * Same choices as the Marathi file, for the same reasons: plain register over
 * administrative vocabulary, ward codes left in Latin script because that is
 * how they appear on every BMC sign and bill, and "वॉर्ड" rather than a
 * translated municipal term because it is what people say.
 *
 * Hindi here is Mumbai Hindi, which is what the audience speaks. Where a
 * Sanskritised word and a commonly spoken one both exist, this file takes the
 * spoken one: "इलाका" rather than "क्षेत्र", "गर्मी" rather than "ऊष्मा".
 *
 * Digits are Latin (24, 60), not Devanagari (२४, ६०). Both are correct
 * Hindi, but every number this interface interpolates at runtime, a rank, a
 * score, a ward count, arrives as a Latin numeral, and a sentence mixing the
 * two scripts looks like a rendering fault. Latin digits are also what appears
 * on a BMC bill, a phone keypad and a bus number, so they are what a reader
 * here is used to.
 *
 * Grid cells are "खाने" (boxes), which is what they look like on the map.
 *
 * The recommendation lookups at the bottom translate text the pipeline sends in
 * English. Citations are not translated: they are author names and paper titles.
 */

import type { Dictionary } from "./index";

const hi: Dictionary = {
  nav: {
    dashboard: "डैशबोर्ड",
    cities: "शहर",
    methodology: "तरीका",
    simulator: "सिम्युलेटर",
    mission: "उद्देश्य",
    contribute: "योगदान दें",
    contact: "संपर्क",
    siteMenu: "साइट मेन्यू",
    openMenu: "मेन्यू खोलें",
    closeMenu: "मेन्यू बंद करें",
    chooseLanguage: "भाषा चुनें",
    homeLabel: "UCIP होम",
    mainNav: "मुख्य",
    mobileNav: "मुख्य (मोबाइल)",
  },

  dashboard: {
    loadingMap: "नक्शा आ रहा है…",
    loading: "आ रहा है…",
    hintLead:
      "रंगों से मुंबई के 24 वॉर्ड का गर्मी के खतरे के हिसाब से क्रम दिखता है। किसी भी वॉर्ड पर, नक्शे में या सूची में, क्लिक करने पर उसका ब्योरा और सुझाए गए उपाय दिखते हैं। ऊपर दाईं ओर से परत बदलें, या",
    hintLink: "तरीका",
    hintTail: " पढ़ें।",
    gotIt: "समझ गया",
    dismissHint: "सूचना हटाएं",
  },

  wardList: {
    heading: "24 वॉर्ड, गर्मी के खतरे के क्रम में",
    intro: "पूरी जानकारी के लिए सूची या नक्शे में किसी वॉर्ड पर क्लिक करें।",
    search: "वॉर्ड या इलाका खोजें…",
    loading: "वॉर्ड आ रहे हैं…",
    noMatch: '"{query}" से कोई वॉर्ड नहीं मिला।',
    followingOne: "1 वॉर्ड सहेजा है",
    followingMany: "{n} वॉर्ड सहेजे हैं",
    compare: "तुलना करें",
    copyLink: "लिंक कॉपी करें",
    copied: "कॉपी हो गया",
    follow: "यह वॉर्ड सहेजें",
    unfollow: "सहेजना बंद करें",
    followAria: "वॉर्ड {ward} सहेजें",
    unfollowAria: "वॉर्ड {ward} सहेजना बंद करें",
  },

  ward: {
    label: "वॉर्ड {ward}",
    loading: "वॉर्ड आ रहा है…",
    loadFailed: "वॉर्ड की जानकारी नहीं आ सकी: {error}",
    mapOf: "{label} का नक्शा",
    boundary: "{label} की सीमा",
    dialogDescription:
      "चुने हुए मुंबई वॉर्ड के लिए गर्मी खतरा सूचकांक, हरियाली की जानकारी और सुझाए गए उपायों का ब्योरा।",

    header: {
      priority: "प्राथमिकता क्रम {rank} ({total} में से)",
      cells: "{n} नक्शे के खाने",
      copyEmbed: "एम्बेड कोड कॉपी करें",
      copyEmbedAria: "वॉर्ड {ward} के लिए एम्बेड कोड कॉपी करें",
      print: "वॉर्ड का सार प्रिंट करें",
      printAria: "वॉर्ड {ward} का सार प्रिंट करें",
      close: "वॉर्ड का ब्योरा बंद करें",
    },

    vsCity: "यह वॉर्ड और पूरा शहर",
    cityValue: "शहर {value}",
    rankOf: "गर्मी के खतरे में {total} में से {rank}",
    hotterThan: "{pct}% से ज़्यादा गरम",
    biggestDriver: "सबसे बड़ा कारण: {factor}।",
    nextDoor: "पड़ोसी वॉर्ड",
    hottest: "सबसे गरम:",
    coolest: "सबसे ठंडा:",
    drivesScore: "स्कोर किन चीज़ों से बनता है",
    contribHelp:
      "लाल रंग इस वॉर्ड का स्कोर बढ़ाता है, हरा घटाता है, शहर के औसत की तुलना में।",
    recommended: "सुझाए गए उपाय",

    factors: {
      LST_C: "ज़मीन की सतह का तापमान",
      NDVI: "हरियाली (NDVI)",
      pop_density_km2: "आबादी का घनत्व",
      elderly_pct: "बुज़ुर्गों का हिस्सा %",
      child_pct: "7 साल से कम के बच्चों का हिस्सा %",
      slum_pct: "बस्तियों का हिस्सा",
      hospital_dist_m: "अस्पताल की दूरी",
      impervious_pct: "निर्माण / पक्की ज़मीन",
    },

    summary: {
      parity:
        "वॉर्ड {ward} में, {cells}, सतह का औसत तापमान {temp} है। यह मुंबई के बाकी हिस्सों जितना ही है।",
      offset:
        "वॉर्ड {ward} में, {cells}, सतह का तापमान {temp} है। यह शहर के औसत से करीब {delta} {direction} है।",
      hotter: "ज़्यादा",
      cooler: "कम",
      oneCell: "एक खाने में",
      manyCells: "{n} खानों में",
      green:
        "हरियाली NDVI सूचकांक पर {ndvi} है, जबकि पूरे शहर में {cityNdvi}। ज़मीन का {built} हिस्सा बना हुआ या पक्का है।",
      people:
        "हर वर्ग किलोमीटर में करीब {density} लोग रहते हैं, और सबसे पास का अस्पताल औसतन {distance} दूर है।",
    },
  },

  layers: {
    tabsLabel: "नक्शे की परत",
    hvi: {
      label: "गर्मी का खतरा",
      caption:
        "गर्मी, आबादी और मदद तक पहुँच को मिलाकर हर वॉर्ड को कितनी जल्दी ठंडक चाहिए।",
    },
    hvi_grid: {
      label: "गर्मी के खाने",
      caption:
        "यही सूचकांक 1 किमी के उस खाने पर जहाँ यह नापा जाता है, 541 खानों का औसत निकालकर 24 वॉर्ड बनाने से पहले।",
    },
    plantability: {
      label: "पेड़ लगाने की गुंजाइश",
      caption:
        "कहाँ पेड़ लगाना पर्यावरण के हिसाब से ठीक है और कहाँ ठंडी छतें ज़्यादा काम आती हैं।",
    },
    ndvi_change: {
      label: "हरियाली में बदलाव",
      caption: "2016-17 के सूखे मौसम के बाद से कहाँ हरियाली बढ़ी या घटी है।",
    },
  },

  legend: {
    hviTitle: "गर्मी खतरा सूचकांक (0-100)",
    gridTitle: "खतरा सूचकांक, 1 किमी खाने (0-100)",
    lessVulnerable: "कम खतरा",
    mostVulnerable: "सबसे ज़्यादा खतरा",
    gridNote: "{cells} खाने, जिनका औसत निकालकर वॉर्ड का स्कोर बनता है।",
    plantTitle: "क्या यहाँ पेड़ लग सकते हैं?",
    plantYes: "हाँ, लगाने लायक",
    plantNo: "नहीं, इसके बजाय ठंडी छतें",
    ndviTitle: "2016-17 से हरियाली",
    gained: "हरियाली बढ़ी",
    stable: "स्थिर",
    lost: "हरियाली घटी",
  },

  map: {
    ariaLabel: "मुंबई वॉर्ड-वार गर्मी खतरा नक्शा",
    layerLoadFailed: "परत लोड नहीं हो सकी: {error}",
    selectWard: "वॉर्ड {ward} चुनें",
    zoomIn: "ज़ूम इन",
    zoomOut: "ज़ूम आउट",
    findMyWard: "मेरा वॉर्ड खोजें",
    finding: "आपका वॉर्ड खोज रहे हैं…",
    findMyWardTitle: "मेरा वॉर्ड खोजें: अपनी लोकेशन इस्तेमाल करें",
    exitFullscreen: "फ़ुलस्क्रीन बंद करें",
    viewFullscreen: "नक्शा फ़ुलस्क्रीन में देखें",
    exitFullscreenTitle: "फ़ुलस्क्रीन बंद करें (Esc)",
    viewFullscreenTitle: "फ़ुलस्क्रीन में देखें",
  },

  locate: {
    unsupported: "इस ब्राउज़र में लोकेशन उपलब्ध नहीं है।",
    denied: "लोकेशन की अनुमति नहीं मिली। आप सूची से अपना वॉर्ड चुन सकते हैं।",
    unavailable: "अभी आपकी लोकेशन पता नहीं चल पाई।",
    timeout: "आपकी लोकेशन खोजने में बहुत समय लगा। दोबारा कोशिश करें।",
    outside: "आप 24 BMC वॉर्ड के बाहर हैं, इसलिए यहाँ कोई वॉर्ड नहीं है।",
    lookup: "आपका वॉर्ड नहीं खोज पाए। थोड़ी देर बाद दोबारा कोशिश करें।",
  },

  compare: {
    heading: "वॉर्ड की तुलना",
    description: "सहेजे गए वॉर्ड की तुलना। यह व्यू URL में सेव रहता है।",
    loadFailed: "वॉर्ड लोड नहीं हो सके: {error}",
    measure: "माप",
    hvi: "HVI",
    cityRank: "शहर में क्रम",
    recommendations: "सुझाए गए उपाय",
    notAvailable: "उपलब्ध नहीं",
  },

  trend: {
    since: "{year} से",
    surfaceTemp: "सतह का तापमान",
    greenCover: "हरियाली",
    lstAria: "सूखे मौसम में ज़मीन की सतह का तापमान",
    ndviAria: "सूखे मौसम का NDVI",
    sparkAria: "{label}: {firstYear} में {first}, {lastYear} में {last}",
    noTrend: "कोई रुझान नहीं मिला ({value})",
    perDecade: "{value} {unit}/दशक",
    warming: "तापमान में बढ़त",
    cooling: "तापमान में गिरावट",
    greening: "हरियाली में बढ़त",
    losingGreen: "हरियाली में गिरावट",
    footSignificant:
      "{n} सूखे मौसमों पर ढलान की गणना (न्यूनतम वर्ग विधि)। यह देखे गए दौर का ब्योरा है, भविष्यवाणी नहीं।",
    footFlat:
      "{n} सूखे मौसमों के Landsat आँकड़ों में इस वॉर्ड में साल-दर-साल के उतार-चढ़ाव से अलग कोई रुझान नहीं दिखता। रेखाएँ असली माप हैं; ढलान पूरेपन के लिए दिखाई गई है, नतीजे के तौर पर नहीं।",
  },

  vintage: {
    refreshed: "जानकारी {date} को अपडेट हुई",
    withWindow: "जानकारी {date} को अपडेट हुई · {window} की सैटेलाइट तस्वीरों से निकाली गई",
  },

  common: {
    close: "बंद करें",
  },

  theme: {
    label: "रंग थीम",
    light: "हल्का",
    dark: "गहरा",
    auto: "ऑटो",
  },

  errors: {
    title: "कुछ गड़बड़ हो गई",
    body: "डैशबोर्ड में अनचाही गड़बड़ हुई। दोबारा लोड करके देखें, बार-बार हो तो हमें बताएँ।",
    retry: "दोबारा कोशिश करें",
  },

  recs: {
    interventions: {
      "Native tree planting + green corridors": "स्थानीय पेड़ लगाना और हरे गलियारे",
      "Cool roofs + reflective pavements + cooling centres":
        "ठंडी छतें, परावर्तक फुटपाथ और शीतल केंद्र",
      "Rain gardens + water-sensitive urban design (WSUD)":
        "रेन गार्डन और पानी का ध्यान रखने वाली शहरी बनावट (WSUD)",
      "Pocket parks": "छोटे पार्क",
      "Cooling centres, priority siting": "शीतल केंद्र, प्राथमिकता से जगह चुनना",
    },
    citations: {
      "Methodology proxy: WorldCover water-distance < 500m (no dedicated hydrology layer in P0)":
        "पद्धति का अनुमान: WorldCover के अनुसार पानी से दूरी 500 मी से कम (P0 में अलग जल-विज्ञान परत नहीं है)",
    },
    rationales: {
      "High vulnerability, low canopy, ecologically suitable for restoration":
        "ज़्यादा खतरा, कम हरियाली, पर्यावरण बहाली के लिए उपयुक्त",
      "High vulnerability, low canopy, but native-grassland/built-up cell: afforestation would backfire ecologically":
        "ज़्यादा खतरा, कम हरियाली, लेकिन यह स्थानीय घास वाला या बना हुआ खाना है: यहाँ पेड़ लगाना पर्यावरण के लिए उल्टा पड़ेगा",
      "Highly impervious cell near mapped water/wetland: runoff and heat compound risk":
        "पानी या दलदली इलाके के पास बहुत पक्का खाना: बहता पानी और गर्मी मिलकर खतरा बढ़ाते हैं",
      "High population density with little existing green/open space":
        "घनी आबादी और हरी या खुली जगह कम",
      "High elderly share combined with poor hospital access":
        "बुज़ुर्गों का हिस्सा ज़्यादा और अस्पताल दूर",
    },
  },
};

export default hi;
