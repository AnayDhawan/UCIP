/**
 * Marathi copy.
 *
 * NOT YET REVIEWED BY A NATIVE SPEAKER. See LOCALE_META in ../locales.ts and
 * the translation section of CONTRIBUTING.md. Corrections are the single most
 * useful contribution this file can receive.
 *
 * Choices worth knowing before correcting anything:
 *
 * Plain register, not administrative Marathi. BMC documents would say
 * "उष्णता असुरक्षितता निर्देशांक" and a resident reading a map on a phone
 * should not have to parse that. Where a Sanskritised term and an everyday one
 * both exist, this file takes the everyday one.
 *
 * Ward codes stay in Latin script. BMC wards are A, B, F/N, G/S and that is how
 * they appear on every official sign, notice and bill. Transliterating them to
 * ए or एफ/एन would be translating an identifier, which helps nobody and breaks
 * the match with what a resident sees on the ground.
 *
 * "वॉर्ड" rather than "प्रभाग". Both are correct and प्रभाग is the formal
 * municipal term, but वॉर्ड is what is said out loud in Mumbai.
 *
 * Digits are Latin (24, 60), not Devanagari (२४, ६०). Both are correct
 * Marathi, but every number this interface interpolates at runtime, a rank, a
 * score, a ward count, arrives as a Latin numeral, and a sentence mixing the
 * two scripts looks like a rendering fault. Latin digits are also what appears
 * on a BMC bill, a phone keypad and a bus number, so they are what a reader
 * here is used to.
 *
 * Grid cells are "चौरस" (squares), which is what they look like on the map.
 *
 * The recommendation lookups at the bottom translate text the pipeline sends in
 * English. Citations are not translated: they are author names and paper titles.
 */

import type { Dictionary } from "./index";

const mr: Dictionary = {
  nav: {
    dashboard: "डॅशबोर्ड",
    cities: "शहरे",
    methodology: "पद्धत",
    simulator: "सिम्युलेटर",
    mission: "उद्देश",
    contribute: "सहभागी व्हा",
    contact: "संपर्क",
    siteMenu: "साइट मेनू",
    openMenu: "मेनू उघडा",
    closeMenu: "मेनू बंद करा",
    chooseLanguage: "भाषा निवडा",
    homeLabel: "UCIP मुख्यपृष्ठ",
    mainNav: "मुख्य",
    mobileNav: "मुख्य (मोबाइल)",
  },

  dashboard: {
    loadingMap: "नकाशा येत आहे…",
    loading: "येत आहे…",
    hintLead:
      "रंगांवरून मुंबईच्या 24 वॉर्डांचा उष्णतेच्या धोक्यानुसार क्रम दिसतो. कोणत्याही वॉर्डवर, नकाशात किंवा यादीत, क्लिक केल्यावर त्याचा तपशील आणि सुचवलेले उपाय दिसतात. वरच्या उजव्या कोपऱ्यातून थर बदला, किंवा",
    hintLink: "पद्धत",
    hintTail: " वाचा.",
    gotIt: "समजले",
    dismissHint: "सूचना बंद करा",
  },

  wardList: {
    heading: "24 वॉर्ड, उष्णतेच्या धोक्यानुसार क्रमाने",
    intro: "पूर्ण माहितीसाठी यादीतील किंवा नकाशावरील वॉर्डवर क्लिक करा.",
    search: "वॉर्ड किंवा भाग शोधा…",
    loading: "वॉर्ड येत आहेत…",
    noMatch: '"{query}" शी जुळणारा वॉर्ड नाही.',
    followingOne: "1 वॉर्ड जतन केला आहे",
    followingMany: "{n} वॉर्ड जतन केले आहेत",
    compare: "तुलना करा",
    copyLink: "दुवा कॉपी करा",
    copied: "कॉपी झाले",
    follow: "हा वॉर्ड जतन करा",
    unfollow: "जतन करणे थांबवा",
    followAria: "वॉर्ड {ward} जतन करा",
    unfollowAria: "वॉर्ड {ward} जतन करणे थांबवा",
  },

  ward: {
    label: "वॉर्ड {ward}",
    loading: "वॉर्ड येत आहे…",
    loadFailed: "वॉर्डची माहिती आणता आली नाही: {error}",
    mapOf: "{label} चा नकाशा",
    boundary: "{label} ची हद्द",
    dialogDescription:
      "निवडलेल्या मुंबई वॉर्डसाठी उष्णता धोका निर्देशांक, हिरवळीची माहिती आणि सुचवलेले उपाय यांचा तपशील.",

    header: {
      priority: "प्राधान्य क्रम {rank} ({total} पैकी)",
      cells: "{n} नकाशा चौरस",
      copyEmbed: "एम्बेड कोड कॉपी करा",
      copyEmbedAria: "वॉर्ड {ward} साठी एम्बेड कोड कॉपी करा",
      print: "वॉर्डचा सारांश छापा",
      printAria: "वॉर्ड {ward} चा सारांश छापा",
      close: "वॉर्डचा तपशील बंद करा",
    },

    vsCity: "हा वॉर्ड आणि संपूर्ण शहर",
    cityValue: "शहर {value}",
    rankOf: "उष्णतेच्या धोक्यात {total} पैकी {rank}",
    hotterThan: "{pct}% पेक्षा जास्त गरम",
    biggestDriver: "सर्वात मोठा घटक: {factor}.",
    nextDoor: "शेजारचे वॉर्ड",
    hottest: "सर्वात गरम:",
    coolest: "सर्वात थंड:",
    drivesScore: "स्कोर कशामुळे ठरतो",
    contribHelp:
      "लाल रंग या वॉर्डचा स्कोर वाढवतो, हिरवा कमी करतो, शहराच्या सरासरीच्या तुलनेत.",
    recommended: "सुचवलेले उपाय",

    factors: {
      LST_C: "जमिनीच्या पृष्ठभागाचे तापमान",
      NDVI: "हिरवळ (NDVI)",
      pop_density_km2: "लोकसंख्येची घनता",
      elderly_pct: "वृद्धांचे प्रमाण %",
      child_pct: "7 वर्षांखालील मुलांचे प्रमाण %",
      slum_pct: "वस्त्यांचे प्रमाण",
      hospital_dist_m: "रुग्णालयापर्यंतचे अंतर",
      impervious_pct: "बांधकाम / पक्की जमीन",
    },

    summary: {
      parity:
        "वॉर्ड {ward} मध्ये, {cells}, पृष्ठभागाचे सरासरी तापमान {temp} आहे. हे मुंबईच्या इतर भागांइतकेच आहे.",
      offset:
        "वॉर्ड {ward} मध्ये, {cells}, पृष्ठभागाचे तापमान {temp} आहे. हे शहराच्या सरासरीपेक्षा सुमारे {delta} {direction} आहे.",
      hotter: "जास्त",
      cooler: "कमी",
      oneCell: "एका चौरसात",
      manyCells: "{n} चौरसांमध्ये",
      green:
        "हिरवळ NDVI निर्देशांकावर {ndvi} आहे, तर संपूर्ण शहरात {cityNdvi}. जमिनीपैकी {built} भाग बांधकाम किंवा फरशीखाली आहे.",
      people:
        "प्रत्येक चौरस किलोमीटरमध्ये सुमारे {density} लोक राहतात, आणि जवळचे रुग्णालय सरासरी {distance} अंतरावर आहे.",
    },
  },

  layers: {
    tabsLabel: "नकाशाचा थर",
    hvi: {
      label: "उष्णतेचा धोका",
      caption:
        "उष्णता, लोकसंख्या आणि मदतीची उपलब्धता एकत्र पाहून प्रत्येक वॉर्डला किती तातडीने थंडावा हवा आहे.",
    },
    hvi_grid: {
      label: "उष्णता चौरस",
      caption:
        "हाच निर्देशांक 1 किमीच्या ज्या चौरसात मोजला जातो तिथे, 541 चौरसांची सरासरी करून 24 वॉर्ड बनवण्यापूर्वी.",
    },
    plantability: {
      label: "झाडे लावण्याची शक्यता",
      caption:
        "कुठे झाडे लावणे पर्यावरणाच्या दृष्टीने योग्य आहे आणि कुठे थंड छपरे जास्त उपयोगी आहेत.",
    },
    ndvi_change: {
      label: "हिरवळीतील बदल",
      caption: "2016-17 च्या कोरड्या हंगामापासून कुठे हिरवळ वाढली किंवा कमी झाली आहे.",
    },
  },

  legend: {
    hviTitle: "उष्णता धोका निर्देशांक (0-100)",
    gridTitle: "उष्णता निर्देशांक, 1 किमी चौरस (0-100)",
    lessVulnerable: "कमी धोका",
    mostVulnerable: "सर्वाधिक धोका",
    gridNote: "{cells} चौरस, ज्यांची सरासरी काढून वॉर्डचा निर्देशांक बनतो.",
    plantTitle: "इथे झाडे लावता येतील का?",
    plantYes: "होय, लावण्यास योग्य",
    plantNo: "नाही, त्याऐवजी थंड छपरे",
    ndviTitle: "2016-17 पासून हिरवळ",
    gained: "हिरवळ वाढली",
    stable: "स्थिर",
    lost: "हिरवळ कमी झाली",
  },

  map: {
    ariaLabel: "मुंबई वॉर्डनिहाय उष्णता धोका नकाशा",
    layerLoadFailed: "थर आणता आला नाही: {error}",
    selectWard: "वॉर्ड {ward} निवडा",
    zoomIn: "मोठे करा",
    zoomOut: "लहान करा",
    findMyWard: "माझा वॉर्ड शोधा",
    finding: "तुमचा वॉर्ड शोधत आहे…",
    findMyWardTitle: "माझा वॉर्ड शोधा: तुमचे स्थान वापरा",
    exitFullscreen: "पूर्ण स्क्रीन बंद करा",
    viewFullscreen: "नकाशा पूर्ण स्क्रीनवर पहा",
    exitFullscreenTitle: "पूर्ण स्क्रीन बंद करा (Esc)",
    viewFullscreenTitle: "पूर्ण स्क्रीनवर पहा",
  },

  locate: {
    unsupported: "या ब्राउझरमध्ये स्थान उपलब्ध नाही.",
    denied: "स्थानाची परवानगी नाकारली गेली. तुम्ही यादीतून तुमचा वॉर्ड निवडू शकता.",
    unavailable: "तुमचे स्थान सध्या समजू शकले नाही.",
    timeout: "तुमचे स्थान शोधायला खूप वेळ लागला. पुन्हा प्रयत्न करा.",
    outside: "तुम्ही 24 BMC वॉर्डांच्या बाहेर आहात, त्यामुळे इथे वॉर्ड नाही.",
    lookup: "तुमचा वॉर्ड शोधता आला नाही. थोड्या वेळाने पुन्हा प्रयत्न करा.",
  },

  compare: {
    heading: "वॉर्डची तुलना",
    description: "जतन केलेल्या वॉर्डांची तुलना. हे दृश्य URL मध्ये जतन होते.",
    loadFailed: "वॉर्ड आणता आले नाहीत: {error}",
    measure: "मोजमाप",
    hvi: "HVI",
    cityRank: "शहरातील क्रम",
    recommendations: "सुचवलेले उपाय",
    notAvailable: "उपलब्ध नाही",
  },

  trend: {
    since: "{year} पासून",
    surfaceTemp: "पृष्ठभागाचे तापमान",
    greenCover: "हिरवळ",
    lstAria: "कोरड्या हंगामातील जमिनीच्या पृष्ठभागाचे तापमान",
    ndviAria: "कोरड्या हंगामातील NDVI",
    sparkAria: "{label}: {firstYear} मध्ये {first}, {lastYear} मध्ये {last}",
    noTrend: "कोणताही कल आढळला नाही ({value})",
    perDecade: "{value} {unit}/दशक",
    warming: "तापमानात वाढ",
    cooling: "तापमानात घट",
    greening: "हिरवळीत वाढ",
    losingGreen: "हिरवळीत घट",
    footSignificant:
      "{n} कोरड्या हंगामांवरील उताराची (किमान वर्ग पद्धत) गणना. हे पाहिलेल्या काळाचे वर्णन आहे, भविष्यवाणी नाही.",
    footFlat:
      "{n} कोरड्या हंगामांच्या Landsat माहितीत या वॉर्डमध्ये वर्षागणिक होणाऱ्या चढउतारांपेक्षा वेगळा कोणताही कल दिसत नाही. रेषा खऱ्या मोजमापांच्या आहेत; उतार पूर्णतेसाठी दाखवला आहे, निष्कर्ष म्हणून नाही.",
  },

  vintage: {
    refreshed: "माहिती {date} रोजी अद्ययावत",
    withWindow: "माहिती {date} रोजी अद्ययावत · {window} या काळातील उपग्रह छायाचित्रांवरून मोजलेली",
  },

  common: {
    close: "बंद करा",
  },

  theme: {
    label: "रंगसंगती",
    light: "उजळ",
    dark: "गडद",
    auto: "आपोआप",
  },

  errors: {
    title: "काहीतरी चूक झाली",
    body: "डॅशबोर्डमध्ये अनपेक्षित चूक झाली. पुन्हा लोड करून पाहा, वारंवार होत असेल तर आम्हाला कळवा.",
    retry: "पुन्हा प्रयत्न करा",
  },

  recs: {
    interventions: {
      "Native tree planting + green corridors": "स्थानिक झाडांची लागवड आणि हरित मार्गिका",
      "Cool roofs + reflective pavements + cooling centres":
        "थंड छपरे, परावर्तक पदपथ आणि शीतकेंद्रे",
      "Rain gardens + water-sensitive urban design (WSUD)":
        "पावसाळी बागा आणि पाण्याचा विचार करणारी शहर रचना (WSUD)",
      "Pocket parks": "छोटी उद्याने",
      "Cooling centres, priority siting": "शीतकेंद्रे, प्राधान्याने जागा निवड",
    },
    citations: {
      "Methodology proxy: WorldCover water-distance < 500m (no dedicated hydrology layer in P0)":
        "पद्धतीचा अंदाज: WorldCover नुसार पाण्यापासूनचे अंतर 500 मी पेक्षा कमी (P0 मध्ये स्वतंत्र जलविज्ञान थर नाही)",
    },
    rationales: {
      "High vulnerability, low canopy, ecologically suitable for restoration":
        "उच्च धोका, कमी झाडोरा, पर्यावरण पुनर्स्थापनेसाठी योग्य",
      "High vulnerability, low canopy, but native-grassland/built-up cell: afforestation would backfire ecologically":
        "उच्च धोका, कमी झाडोरा, पण हा स्थानिक गवताळ किंवा बांधकाम केलेला चौरस आहे: इथे वृक्षारोपण केल्यास पर्यावरणाला उलट फटका बसेल",
      "Highly impervious cell near mapped water/wetland: runoff and heat compound risk":
        "जलस्रोत किंवा पाणथळीजवळचा, पाणी जिरू न देणारा चौरस: वाहून जाणारे पाणी आणि उष्णता मिळून धोका वाढतो",
      "High population density with little existing green/open space":
        "दाट लोकसंख्या आणि हिरवी किंवा मोकळी जागा कमी",
      "High elderly share combined with poor hospital access":
        "वृद्धांचे प्रमाण जास्त आणि रुग्णालय दूर",
    },
  },
};

export default mr;
