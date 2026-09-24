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
    language: "भाषा",
    chooseLanguage: "भाषा चुनें",
  },

  dashboard: {
    title: "मुंबई में गर्मी का खतरा",
    loadingMap: "नक्शा आ रहा है…",
    loading: "आ रहा है…",
    dismissHint: "सूचना हटाएं",
  },

  wardList: {
    heading: "24 वॉर्ड, गर्मी के खतरे के क्रम में",
    search: "वॉर्ड या इलाका खोजें…",
    loading: "वॉर्ड आ रहे हैं…",
    noResults: "इस खोज से कोई वॉर्ड नहीं मिला।",
    follow: "यह वॉर्ड सहेजें",
    unfollow: "सहेजना बंद करें",
    copyLink: "लिंक कॉपी करें",
    linkCopied: "लिंक कॉपी हो गया",
  },

  ward: {
    label: "वॉर्ड {ward}",
    rank: "क्रम",
    rankOf: "{total} में से {rank}",
    score: "गर्मी खतरा सूचकांक",
    cells: "नक्शे के खाने",
    close: "बंद करें",
    factors: {
      LST_C: "ज़मीन की सतह का तापमान",
      NDVI: "हरियाली",
      pop_density_km2: "आबादी का घनत्व",
      elderly_pct: "60 साल से ऊपर के लोगों का हिस्सा",
      child_pct: "7 साल से कम उम्र के बच्चों का हिस्सा",
      slum_pct: "बस्तियों का हिस्सा",
      hospital_dist_m: "अस्पताल की दूरी",
      impervious_pct: "पक्की ज़मीन",
    },
  },

  layers: {
    heading: "नक्शे की परत",
    hvi: "गर्मी का खतरा",
    plantable: "पेड़ लगाने लायक जगह",
    ndviChange: "हरियाली में बदलाव",
    temperature: "सतह का तापमान",
  },

  legend: {
    lower: "कम",
    higher: "ज़्यादा",
    noData: "जानकारी नहीं",
  },

  vintage: {
    refreshed: "जानकारी {date} को अपडेट हुई",
    imagery: "{window} की सैटेलाइट तस्वीरें",
    unknown: "अपडेट की तारीख अभी दर्ज नहीं है",
    snapshot: "पिछली प्रकाशित जानकारी दिखाई जा रही है",
  },

  caveats: {
    singleFactor:
      "इस वॉर्ड का सूचकांक ज़्यादातर एक ही चीज़ ({factor}) पर टिका है, इसलिए इसे कई चीज़ों का जोड़ न मानकर वही चीज़ समझकर पढ़ें।",
    rankUncertain:
      "बीच के क्रमांकों में ख़ास फ़र्क़ नहीं है। दो-तीन क्रम का अंतर कोई अंतर नहीं मानें।",
    proxy: "यह परत अनुमान पर आधारित है, सीधी माप नहीं।",
  },

  errors: {
    title: "कुछ गड़बड़ हो गई",
    body: "पेज नहीं खुल सका। दोबारा लोड करने पर आमतौर पर चल जाता है।",
    retry: "दोबारा कोशिश करें",
    offline: "लगता है आप ऑफ़लाइन हैं।",
  },

  footer: {
    dataLicence: "डेटा लाइसेंस",
    sourceCode: "सोर्स कोड",
    methodology: "यह कैसे निकाला जाता है",
  },
};

export default hi;
