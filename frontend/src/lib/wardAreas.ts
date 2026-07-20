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

export function areasForWard(wardId: string): string[] {
  return WARD_AREAS[wardId] ?? [];
}
