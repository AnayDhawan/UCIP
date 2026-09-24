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
    language: "भाषा",
    chooseLanguage: "भाषा निवडा",
  },

  dashboard: {
    title: "मुंबईतील उष्णतेचा धोका",
    loadingMap: "नकाशा येत आहे…",
    loading: "येत आहे…",
    dismissHint: "सूचना बंद करा",
  },

  wardList: {
    heading: "24 वॉर्ड, उष्णतेच्या धोक्यानुसार क्रमाने",
    search: "वॉर्ड किंवा भाग शोधा…",
    loading: "वॉर्ड येत आहेत…",
    noResults: "या शोधाशी जुळणारा वॉर्ड नाही.",
    follow: "हा वॉर्ड जतन करा",
    unfollow: "जतन करणे थांबवा",
    copyLink: "दुवा कॉपी करा",
    linkCopied: "दुवा कॉपी झाला",
  },

  ward: {
    label: "वॉर्ड {ward}",
    rank: "क्रम",
    rankOf: "{total} पैकी {rank}",
    score: "उष्णता धोका निर्देशांक",
    cells: "नकाशा चौरस",
    close: "बंद करा",
    factors: {
      LST_C: "जमिनीच्या पृष्ठभागाचे तापमान",
      NDVI: "हिरवळ",
      pop_density_km2: "लोकसंख्येची घनता",
      elderly_pct: "60 वर्षांवरील लोकांचे प्रमाण",
      child_pct: "7 वर्षांखालील मुलांचे प्रमाण",
      slum_pct: "वस्त्यांचे प्रमाण",
      hospital_dist_m: "रुग्णालयापर्यंतचे अंतर",
      impervious_pct: "बांधकामाखालील जमीन",
    },
  },

  layers: {
    heading: "नकाशाचा थर",
    hvi: "उष्णतेचा धोका",
    plantable: "झाडे लावण्यासाठी योग्य जागा",
    ndviChange: "हिरवळीतील बदल",
    temperature: "पृष्ठभागाचे तापमान",
  },

  legend: {
    lower: "कमी",
    higher: "जास्त",
    noData: "माहिती नाही",
  },

  vintage: {
    refreshed: "माहिती {date} रोजी अद्ययावत",
    imagery: "{window} या काळातील उपग्रह छायाचित्रे",
    unknown: "अद्ययावत करण्याची तारीख अजून नोंदलेली नाही",
    snapshot: "शेवटची प्रसिद्ध केलेली माहिती दाखवत आहोत",
  },

  caveats: {
    singleFactor:
      "या वॉर्डचा निर्देशांक मुख्यतः एकाच घटकावर ({factor}) अवलंबून आहे, त्यामुळे तो अनेक घटकांची बेरीज न मानता तोच घटक समजून वाचा.",
    rankUncertain:
      "मधल्या क्रमांकांमध्ये फारसा फरक नाही. दोन-तीन क्रमांकांचा फरक म्हणजे फरक नाही असे समजा.",
    proxy: "हा थर अंदाजावर आधारित आहे, थेट मोजमाप नाही.",
  },

  errors: {
    title: "काहीतरी चूक झाली",
    body: "पान उघडता आले नाही. पुन्हा लोड केल्यावर बहुधा चालेल.",
    retry: "पुन्हा प्रयत्न करा",
    offline: "तुम्ही ऑफलाइन असल्याचे दिसते.",
  },

  footer: {
    dataLicence: "माहितीचे परवाने",
    sourceCode: "सोर्स कोड",
    methodology: "हे कसे मोजले जाते",
  },
};

export default mr;
