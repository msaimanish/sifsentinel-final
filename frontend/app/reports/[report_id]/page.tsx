"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type SimilarReport = {
  report_id: string;
  similarity: number;
  event_date?: string;
  employer?: string;
  city?: string;
  state?: string;
  description?: string;
  sif_probability?: number | null;
  sif_label?: string | null;
  life_saving_rules?: string[];
  activity?: string | null;
  hazard?: string | null;
  exposure?: string | null;
  barrier?: string | null;
  barrier_failure?: string | null;
  priority_score?: number | null;
  priority_band?: string | null;
};

type Analysis = {
  report: {
    report_id: string;
    event_date: string | null;
    employer: string | null;
    city: string | null;
    state: string | null;
    naics: string | null;
    event: string | null;
    nature: string | null;
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

  similar_reports: {
    report_id: string;
    similarity: number;
  }[];

  status: {
    has_prediction: boolean;
    has_embedding: boolean;
    has_intelligence: boolean;
  };
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

function formatPercent(value: number | null) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function priorityClass(priority?: string | null) {
  switch (priority) {
    case "Critical":
      return "border-red-500/20 bg-red-500/10 text-red-300";

    case "High":
      return "border-orange-500/20 bg-orange-500/10 text-orange-300";

    case "Moderate":
      return "border-yellow-500/20 bg-yellow-500/10 text-yellow-300";

    default:
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }
}

function sifClass(label?: string | null) {
  if (label === "YES") {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  return "border-zinc-500/20 bg-zinc-500/10 text-zinc-400";
}

function FeatureCard({
  title,
  value,
  accent = false,
}: {
  title: string;
  value: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        accent
          ? "border-cyan-400/15 bg-cyan-400/[0.03]"
          : "border-white/10 bg-white/[0.03]"
      }`}
    >
      <div className="mb-2 text-[11px] uppercase tracking-[0.15em] text-zinc-600">
        {title}
      </div>

      <div className="text-sm leading-6 text-zinc-200">
        {value || (
          <span className="text-zinc-600">
            Not detected
          </span>
        )}
      </div>
    </div>
  );
}

function Tag({
  children,
  type = "default",
}: {
  children: React.ReactNode;
  type?: "default" | "risk" | "sif" | "cyan";
}) {
  const styles = {
    default:
      "border-white/10 bg-black/20 text-zinc-400",
    risk:
      "border-red-500/20 bg-red-500/10 text-red-300",
    sif:
      "border-yellow-500/20 bg-yellow-500/10 text-yellow-300",
    cyan:
      "border-cyan-400/20 bg-cyan-400/10 text-cyan-300",
  };

  return (
    <span
      className={`rounded-lg border px-2.5 py-1 text-[11px] ${styles[type]}`}
    >
      {children}
    </span>
  );
}

export default function ReportPage({
  params,
}: {
  params: Promise<{ report_id: string }>;
}) {
  const [analysis, setAnalysis] = useState<Analysis | null>(
    null,
  );

  const [similarReports, setSimilarReports] = useState<
    SimilarReport[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadReport() {
      try {
        const { report_id } = await params;

        const id = encodeURIComponent(report_id);

        const [analysisResponse, similarResponse] =
          await Promise.all([
            fetch(`${API_URL}/reports/${id}/analysis`, {
              cache: "no-store",
            }),
            fetch(
              `${API_URL}/reports/${id}/similar?limit=5`,
              {
                cache: "no-store",
              },
            ),
          ]);

        if (!analysisResponse.ok) {
          throw new Error(
            `Could not load report (${analysisResponse.status})`,
          );
        }

        const analysisData: Analysis =
          await analysisResponse.json();

        setAnalysis(analysisData);

        if (similarResponse.ok) {
          const similarData =
            await similarResponse.json();

          setSimilarReports(
            similarData.similar_reports ?? [],
          );
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Could not load report.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadReport();
  }, [params]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#080808] text-white">
        <div className="mx-auto max-w-7xl px-6 py-10 text-sm text-zinc-500">
          Loading report intelligence...
        </div>
      </main>
    );
  }

  if (error || !analysis) {
    return (
      <main className="min-h-screen bg-[#080808] px-6 py-10 text-white">
        <div className="mx-auto max-w-7xl">
          <Link
            href="/reports"
            className="text-sm text-zinc-500 transition hover:text-white"
          >
            ← Back to Reports
          </Link>

          <div className="mt-8 rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-red-300">
            {error || "Report not found."}
          </div>
        </div>
      </main>
    );
  }

  const report = analysis.report;
  const sif = analysis.sif_assessment;
  const safety = analysis.safety_features;
  const risk = analysis.risk;

  const precursorCount =
    (safety.activity ? 1 : 0) +
    safety.hazards.length +
    (safety.exposure ? 1 : 0) +
    safety.barriers.length +
    safety.barrier_failures.length;

  return (
    <main className="min-h-screen bg-[#080808] text-white">
      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-8">

        {/* HEADER */}

        <header className="mb-8 flex flex-col gap-6 border-b border-white/10 pb-7 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="h-3 w-3 rounded-full bg-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.7)]" />

              <h1 className="text-2xl font-semibold tracking-tight">
                SIFSentinel
              </h1>
            </div>

            <p className="mt-2 text-sm text-zinc-500">
              Serious Injury &amp; Fatality precursor intelligence
            </p>
          </div>

          <nav className="flex flex-wrap items-center gap-1 rounded-2xl border border-white/10 bg-white/[0.025] p-1">
            <Link
              href="/"
              className="rounded-xl px-4 py-2 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
            >
              Dashboard
            </Link>

            <Link
              href="/reports"
              className="rounded-xl bg-white/10 px-4 py-2 text-sm text-white"
            >
              Reports
            </Link>

            <Link
              href="/upload"
              className="rounded-xl px-4 py-2 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
            >
              Upload Report
            </Link>
          </nav>
        </header>

        {/* TITLE */}

        <div className="mb-7">
          <Link
            href="/reports"
            className="text-sm text-zinc-600 transition hover:text-white"
          >
            ← Back to Reports
          </Link>

          <div className="mt-5 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="font-mono text-xs text-cyan-400">
                {report.report_id}
              </p>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight">
                Report Intelligence
              </h2>

              <p className="mt-2 max-w-2xl text-sm text-zinc-500">
                Structured safety signals extracted from the incident
                narrative and matched against historical reports.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {sif.label && (
                <span
                  className={`rounded-full border px-3.5 py-2 text-xs font-medium ${sifClass(
                    sif.label,
                  )}`}
                >
                  SIF {sif.label}
                </span>
              )}

              {risk.band && (
                <span
                  className={`rounded-full border px-3.5 py-2 text-xs font-medium ${priorityClass(
                    risk.band,
                  )}`}
                >
                  {risk.band} Priority
                </span>
              )}
            </div>
          </div>
        </div>

        {/* EXECUTIVE SUMMARY */}

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-zinc-600">
              SIF signal
            </p>

            <p className="mt-3 text-4xl font-semibold">
              {formatPercent(sif.probability)}
            </p>

            <p className="mt-2 text-xs text-zinc-600">
              {sif.model_version || "Model unavailable"}
            </p>
          </div>

          <div
            className={`rounded-2xl border p-6 ${priorityClass(
              risk.band,
            )}`}
          >
            <p className="text-xs uppercase tracking-[0.15em] opacity-60">
              Priority
            </p>

            <p className="mt-3 text-4xl font-semibold">
              {risk.score !== null
                ? risk.score.toFixed(1)
                : "—"}
            </p>

            <p className="mt-2 text-xs opacity-60">
              {risk.band || "Not scored"}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-zinc-600">
              Precursors
            </p>

            <p className="mt-3 text-4xl font-semibold">
              {precursorCount}
            </p>

            <p className="mt-2 text-xs text-zinc-600">
              Extracted safety signals
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
            <p className="text-xs uppercase tracking-[0.15em] text-zinc-600">
              Semantic match
            </p>

            <p className="mt-3 text-4xl font-semibold">
              {similarReports.length}
            </p>

            <p className="mt-2 text-xs text-zinc-600">
              Historical matches available
            </p>
          </div>
        </section>

        {/* INCIDENT CONTEXT */}

        <section className="mt-6">
          <div className="mb-4">
            <h3 className="text-lg font-medium">
              Incident Context
            </h3>

            <p className="mt-1 text-sm text-zinc-500">
              Core metadata associated with this report.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <FeatureCard
              title="Event Date"
              value={report.event_date || "Unknown"}
            />

            <FeatureCard
              title="Employer"
              value={report.employer || "Unknown"}
            />

            <FeatureCard
              title="Location"
              value={
                [report.city, report.state]
                  .filter(Boolean)
                  .join(", ") || "Unknown"
              }
            />

            <FeatureCard
              title="NAICS"
              value={report.naics || "Unknown"}
            />
          </div>
        </section>

        {/* ORIGINAL REPORT */}

        <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-medium">
                Original Report
              </h3>

              <p className="mt-1 text-sm text-zinc-500">
                Source narrative used for analysis.
              </p>
            </div>

            {report.event && (
              <Tag>{report.event}</Tag>
            )}
          </div>

          <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-5">
            <p className="text-sm leading-7 text-zinc-300">
              {report.description}
            </p>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <FeatureCard
              title="Nature"
              value={report.nature}
            />

            <FeatureCard
              title="Event"
              value={report.event}
            />
          </div>
        </section>

        {/* PRECURSOR INTELLIGENCE */}

        <section className="mt-8">
          <div className="mb-4">
            <h3 className="text-lg font-medium">
              Precursor Intelligence
            </h3>

            <p className="mt-1 text-sm text-zinc-500">
              Safety-relevant activities, hazards, exposures and
              barrier conditions extracted from the narrative.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <FeatureCard
              title="Activity"
              value={safety.activity}
              accent
            />

            <FeatureCard
              title="Hazard"
              value={safety.hazards.join("; ")}
            />

            <FeatureCard
              title="Exposure"
              value={safety.exposure}
            />

            <FeatureCard
              title="Barrier"
              value={safety.barriers.join("; ")}
            />

            <FeatureCard
              title="Barrier Failure"
              value={safety.barrier_failures.join("; ")}
            />

            <FeatureCard
              title="Processing Status"
              value={
                <div className="flex flex-wrap gap-2">
                  {analysis.status.has_intelligence && (
                    <Tag type="cyan">
                      Intelligence
                    </Tag>
                  )}

                  {analysis.status.has_prediction && (
                    <Tag type="cyan">
                      SIF Model
                    </Tag>
                  )}

                  {analysis.status.has_embedding && (
                    <Tag type="cyan">
                      Embedding
                    </Tag>
                  )}
                </div>
              }
            />
          </div>
        </section>

        {/* LIFE-SAVING RULES */}

        <section className="mt-8 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
          <div>
            <h3 className="text-lg font-medium">
              IOGP Life-Saving Rules
            </h3>

            <p className="mt-1 text-sm text-zinc-500">
              Rules associated with the detected safety precursors.
            </p>
          </div>

          {safety.life_saving_rules.length === 0 ? (
            <p className="mt-5 text-sm text-zinc-600">
              No Life-Saving Rule detected.
            </p>
          ) : (
            <div className="mt-5 flex flex-wrap gap-2">
              {safety.life_saving_rules.map((rule) => (
                <Tag key={rule} type="cyan">
                  {rule}
                </Tag>
              ))}
            </div>
          )}
        </section>

        {/* SIMILAR REPORTS */}

        <section className="mt-8">
          <div className="mb-4">
            <h3 className="text-lg font-medium">
              Similar Historical Reports
            </h3>

            <p className="mt-1 text-sm text-zinc-500">
              Retrieved using semantic similarity from the report
              embeddings.
            </p>
          </div>

          <div className="space-y-3">
            {similarReports.length === 0 ? (
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-sm text-zinc-500">
                No similar reports available.
              </div>
            ) : (
              similarReports.map((similar) => (
                <Link
                  key={similar.report_id}
                  href={`/reports/${encodeURIComponent(
                    similar.report_id,
                  )}`}
                  className="group block rounded-2xl border border-white/10 bg-white/[0.025] p-5 transition hover:border-cyan-400/20 hover:bg-white/[0.04]"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-cyan-400">
                          {similar.report_id}
                        </span>

                        {similar.priority_band && (
                          <span
                            className={`rounded-full border px-2 py-1 text-[10px] ${priorityClass(
                              similar.priority_band,
                            )}`}
                          >
                            {similar.priority_band}
                          </span>
                        )}

                        {similar.sif_label && (
                          <span
                            className={`rounded-full border px-2 py-1 text-[10px] ${sifClass(
                              similar.sif_label,
                            )}`}
                          >
                            SIF {similar.sif_label}
                          </span>
                        )}
                      </div>

                      <p className="mt-3 text-sm leading-6 text-zinc-400">
                        {similar.description ||
                          "Historical report with similar semantic context."}
                      </p>

                      <div className="mt-3 text-xs text-zinc-600">
                        {similar.event_date ||
                          "Unknown date"}
                        {similar.employer
                          ? ` · ${similar.employer}`
                          : ""}
                      </div>
                    </div>

                    <div className="shrink-0 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1.5 text-xs text-cyan-300">
                      {(similar.similarity * 100).toFixed(
                        1,
                      )}
                      % similar
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </section>

        {/* DISCLAIMER */}

        <div className="mt-10 border-t border-white/10 pt-5">
          <p className="text-xs leading-5 text-zinc-600">
            SIF probability is a model-generated ranking signal,
            not a calibrated probability of serious injury or
            fatality. Precursor extraction combines NLP models
            and deterministic safety rules. Findings should be
            reviewed in operational context before safety decisions
            are made.
          </p>
        </div>
      </div>
    </main>
  );
}