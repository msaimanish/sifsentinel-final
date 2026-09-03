const API_URL = "http://localhost:8000";

export interface Overview {
  total_reports: number;
  sif_potential: number;
  high_priority: number;
  critical_priority: number;
  average_sif_probability?: number | null;
}

export interface TrendPoint {
  year: number;
  reports: number;
  sif_potential: number;
}

export interface Activity {
  activity: string;
  count: number;
  priority_score: number | null;
}

export interface Location {
  location: string;
  count: number;
  priority_score: number | null;
}

export interface LSR {
  rule: string;
  count: number;
  priority_score: number | null;
}

export interface PriorityDistribution {
  band: string;
  count: number;
}

export interface PriorityReport {
  report_id: string;
  event_date: string;
  employer: string;
  location: string;
  state: string;
  description: string;

  sif_probability: number | null;
  sif_label: string | null;

  activity: string | null;
  hazard: string | null;
  barrier_failure: string | null;

  priority_score: number | null;
  priority_band: string | null;
}

export interface SimilarReport {
  report_id: string;
  similarity: number;
  event_date: string;
  employer: string;
  city: string;
  state: string;
  description: string;

  sif_probability: number | null;
  sif_label: string | null;

  life_saving_rules: string[];
  activity: string | null;
  hazard: string | null;
  exposure: string | null;
  barrier: string | null;
  barrier_failure: string | null;

  priority_score: number | null;
  priority_band: string | null;
}

export interface ReportAnalysis {
  report: {
    report_id: string;
    event_date: string;
    employer: string;
    city: string;
    state: string;
    naics: string;
    event: string;
    nature: string;
    description: string;
  };

  sif_assessment: {
    probability: number | null;
    label: string | null;
    model_version: string | null;
  };

  safety_features: {
    activity: string | null;
    hazards: string[];
    exposure: string | null;
    barriers: string[];
    barrier_failures: string[];
    life_saving_rules: string[];
  };

  risk: {
    score: number | null;
    band: string | null;
  };

  similar_reports: SimilarReport[];

  status: {
    has_prediction: boolean;
    has_embedding: boolean;
    has_intelligence: boolean;
  };
}

async function fetchAPI<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status}`
    );
  }

  return response.json();
}

export const api = {
  overview: () =>
    fetchAPI<Overview>("/analytics/overview"),

  trends: () =>
    fetchAPI<TrendPoint[]>("/analytics/trends"),

  activities: (limit = 10) =>
    fetchAPI<Activity[]>(
      `/analytics/activities?limit=${limit}`
    ),

  locations: (limit = 10) =>
    fetchAPI<Location[]>(
      `/analytics/locations?limit=${limit}`
    ),

  lsr: (limit = 10) =>
    fetchAPI<LSR[]>(
      `/analytics/lsr?limit=${limit}`
    ),

  priorityDistribution: () =>
    fetchAPI<PriorityDistribution[]>(
      "/analytics/priority-distribution"
    ),

  priorityReports: (limit = 10) =>
    fetchAPI<PriorityReport[]>(
      `/analytics/priority-reports?limit=${limit}`
    ),

  reportAnalysis: (reportId: string) =>
    fetchAPI<ReportAnalysis>(
      `/reports/${encodeURIComponent(reportId)}/analysis`
    ),
};