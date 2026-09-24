/**
 * Localities/neighbourhoods within each of Mumbai's 24 BMC administrative wards.
 * Publicly documented civic geography (BMC ward structure), included so a
 * resident can find their own area rather than needing to know the ward code.
 * Not exhaustive, the well-known localities per ward.
 */
export const WARD_AREAS: Record<string, string[]> = {
  A: ["Colaba", "Fort", "Churchgate", "Marine Drive", "Cuffe Parade"],
  B: ["Dongri", "Mandvi", "Umerkhadi"],
  C: ["Marine Lines", "Kalbadevi", "Bhuleshwar", "Chira Bazar"],
  D: ["Malabar Hill", "Walkeshwar", "Tardeo", "Grant Road", "Nana Chowk"],
  E: ["Byculla", "Mazgaon", "Bhoiwada"],
  "F/S": ["Parel", "Lalbaug", "Sewri"],
  "F/N": ["Matunga", "Sion", "Wadala"],
  "G/S": ["Worli", "Prabhadevi"],
  "G/N": ["Dadar", "Mahim", "Dharavi"],
  "H/E": ["Bandra East", "Khar East", "Santacruz East"],
  "H/W": ["Bandra West", "Khar West", "Santacruz West"],
  "K/E": ["Andheri East", "Marol", "Chakala", "Vile Parle East"],
  "K/W": ["Andheri West", "Juhu", "Vile Parle West", "Versova"],
  "P/S": ["Goregaon"],
  "P/N": ["Malad"],
  "R/S": ["Kandivali"],
  "R/N": ["Dahisar", "Borivali (east)"],
  "R/C": ["Borivali", "Magathane"],
  L: ["Kurla"],
  "M/E": ["Govandi", "Mankhurd", "Deonar"],
  "M/W": ["Chembur", "Anushakti Nagar"],
  N: ["Ghatkopar", "Vikhroli"],
  S: ["Bhandup", "Powai", "Kanjurmarg"],
  T: ["Mulund"],
};

/**
 * The same localities in Marathi and Hindi, in the same order as WARD_AREAS so
 * that index i is the same place in every language.
 *
 * Standard local forms of place names, not translations: Dadar is दादर and
 * Colaba is कुलाबा. Not yet reviewed by a native speaker, like the rest of the
 * copy in lib/i18n. Where Marathi and Hindi differ it is spelling, for example
 * Sion (शीव in Marathi usage, सायन in Hindi) and Bandra (वांद्रे against बांद्रा).
 */
const WARD_AREAS_LOCAL: Record<"mr" | "hi", Record<string, string[]>> = {
  mr: {
    A: ["कुलाबा", "फोर्ट", "चर्चगेट", "मरीन ड्राइव्ह", "कफ परेड"],
    B: ["डोंगरी", "मांडवी", "उमरखाडी"],
    C: ["मरीन लाईन्स", "काळबादेवी", "भुलेश्वर", "चिरा बाजार"],
    D: ["मलबार हिल", "वाळकेश्वर", "ताडदेव", "ग्रँट रोड", "नाना चौक"],
    E: ["भायखळा", "माझगाव", "भोईवाडा"],
    "F/S": ["परळ", "लालबाग", "शिवडी"],
    "F/N": ["माटुंगा", "शीव", "वडाळा"],
    "G/S": ["वरळी", "प्रभादेवी"],
    "G/N": ["दादर", "माहीम", "धारावी"],
    "H/E": ["वांद्रे पूर्व", "खार पूर्व", "सांताक्रूझ पूर्व"],
    "H/W": ["वांद्रे पश्चिम", "खार पश्चिम", "सांताक्रूझ पश्चिम"],
    "K/E": ["अंधेरी पूर्व", "मरोळ", "चकाला", "विलेपार्ले पूर्व"],
    "K/W": ["अंधेरी पश्चिम", "जुहू", "विलेपार्ले पश्चिम", "वर्सोवा"],
    "P/S": ["गोरेगाव"],
    "P/N": ["मालाड"],
    "R/S": ["कांदिवली"],
    "R/N": ["दहिसर", "बोरिवली (पूर्व)"],
    "R/C": ["बोरिवली", "मागाठाणे"],
    L: ["कुर्ला"],
    "M/E": ["गोवंडी", "मानखुर्द", "देवनार"],
    "M/W": ["चेंबूर", "अणुशक्ती नगर"],
    N: ["घाटकोपर", "विक्रोळी"],
    S: ["भांडुप", "पवई", "कांजूरमार्ग"],
    T: ["मुलुंड"],
  },
  hi: {
    A: ["कोलाबा", "फोर्ट", "चर्चगेट", "मरीन ड्राइव", "कफ परेड"],
    B: ["डोंगरी", "मांडवी", "उमरखाड़ी"],
    C: ["मरीन लाइंस", "कालबादेवी", "भुलेश्वर", "चिरा बाज़ार"],
    D: ["मलबार हिल", "वालकेश्वर", "तारदेव", "ग्रांट रोड", "नाना चौक"],
    E: ["भायखला", "माझगांव", "भोईवाड़ा"],
    "F/S": ["परेल", "लालबाग", "शिवड़ी"],
    "F/N": ["माटुंगा", "सायन", "वडाला"],
    "G/S": ["वरली", "प्रभादेवी"],
    "G/N": ["दादर", "माहिम", "धारावी"],
    "H/E": ["बांद्रा पूर्व", "खार पूर्व", "सांताक्रूज़ पूर्व"],
    "H/W": ["बांद्रा पश्चिम", "खार पश्चिम", "सांताक्रूज़ पश्चिम"],
    "K/E": ["अंधेरी पूर्व", "मरोल", "चकाला", "विले पार्ले पूर्व"],
    "K/W": ["अंधेरी पश्चिम", "जुहू", "विले पार्ले पश्चिम", "वर्सोवा"],
    "P/S": ["गोरेगांव"],
    "P/N": ["मलाड"],
    "R/S": ["कांदिवली"],
    "R/N": ["दहिसर", "बोरीवली (पूर्व)"],
    "R/C": ["बोरीवली", "मागाठाणे"],
    L: ["कुर्ला"],
    "M/E": ["गोवंडी", "मानखुर्द", "देवनार"],
    "M/W": ["चेंबूर", "अणुशक्ति नगर"],
    N: ["घाटकोपर", "विक्रोली"],
    S: ["भांडुप", "पवई", "कांजूरमार्ग"],
    T: ["मुलुंड"],
  },
};

/**
 * The localities for a ward, in the reader's language. Falls back to English
 * for a language or a ward with no entry, which is the right failure: a place
 * name in the wrong script is still a place name.
 */
export function areasForWard(wardId: string, locale: string = "en"): string[] {
  if (locale === "mr" || locale === "hi") {
    const local = WARD_AREAS_LOCAL[locale][wardId];
    if (local) return local;
  }
  return WARD_AREAS[wardId] ?? [];
}

/**
 * Every spelling of a ward's localities, joined and lower-cased, for search.
 *
 * Search matches all languages at once whatever the interface language is. A
 * resident using the Marathi interface may still type "Dadar", and someone on
 * the English one may paste दादर, and neither should return nothing.
 */
export function searchableAreas(wardId: string): string {
  return [
    ...(WARD_AREAS[wardId] ?? []),
    ...(WARD_AREAS_LOCAL.mr[wardId] ?? []),
    ...(WARD_AREAS_LOCAL.hi[wardId] ?? []),
  ]
    .join(" ")
    .toLowerCase();
}
