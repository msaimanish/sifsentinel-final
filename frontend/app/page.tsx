"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  api,
  Overview,
  Activity,
  LSR,
  PriorityDistribution,
  PriorityReport,
} from "@/lib/api";

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function riskClass(band: string | null | undefined) {
  switch (band) {
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

function StatCard({
  label,
  value,
  description,
  accent,
}: {
  label: string;
  value: string;
  description: string;
  accent?: string;
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.035] p-6 transition hover:border-white/15 hover:bg-white/[0.05]">
      <div
        className={`absolute inset-x-0 top-0 h-px ${
          accent ?? "bg-white/10"
        }`}
      />

      <p className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
        {label}
      </p>

      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>

      <p className="mt-2 text-xs text-zinc-600">
        {description}
      </p>
    </div>
  );
}

function Panel({
  title,
  subtitle,
  children,
  className = "",
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-2xl border border-white/10 bg-white/[0.03] p-6 ${className}`}
    >
      <div className="mb-6">
        <h2 className="text-base font-medium text-white">
          {title}
        </h2>

        {subtitle && (
          <p className="mt-1 text-sm text-zinc-500">
            {subtitle}
          </p>
        )}
      </div>

      {children}
    </section>
  );
}

export default function Dashboard() {
  const [overview, setOverview] =
    useState<Overview | null>(null);

  const [activities, setActivities] =
    useState<Activity[]>([]);

  const [lsr, setLSR] =
    useState<LSR[]>([]);

  const [priorityDistribution, setPriorityDistribution] =
    useState<PriorityDistribution[]>([]);

  const [priorityReports, setPriorityReports] =
    useState<PriorityReport[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [
          overviewData,
          activitiesData,
          lsrData,
          distributionData,
          reportsData,
        ] = await Promise.all([
          api.overview(),
          api.activities(8),
          api.lsr(8),
          api.priorityDistribution(),
          api.priorityReports(8),
        ]);

        setOverview(overviewData);
        setActivities(activitiesData);
        setLSR(lsrData);
        setPriorityDistribution(distributionData);
        setPriorityReports(reportsData);
      } catch (err) {
        console.error(err);

        setError(
          "Unable to load SIFSentinel analytics.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#080808] px-6 py-10 text-white">
        <div className="mx-auto max-w-7xl">
          <div className="animate-pulse">
            <div className="h-8 w-48 rounded bg-white/5" />
            <div className="mt-3 h-4 w-80 rounded bg-white/5" />

            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((item) => (
                <div
                  key={item}
                  className="h-32 rounded-2xl border border-white/10 bg-white/[0.03]"
                />
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#080808] px-6 py-10 text-white">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
            <p className="text-red-300">{error}</p>
            <p className="mt-2 text-sm text-zinc-500">
              Make sure the SIFSentinel services are running.
            </p>
          </div>
        </div>
      </main>
    );
  }

  const totalReports =
    overview?.total_reports ?? 0;

  const sifSignals =
    overview?.sif_potential ?? 0;

  const sifRate =
    totalReports > 0
      ? (sifSignals / totalReports) * 100
      : 0;

  const critical =
    overview?.critical_priority ?? 0;

  const high =
    overview?.high_priority ?? 0;

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

            <p className="mt-2 max-w-xl text-sm text-zinc-500">
              Serious Injury &amp; Fatality precursor intelligence
              from incident and near-miss reports.
            </p>
          </div>

          <nav className="flex flex-wrap items-center gap-1 rounded-2xl border border-white/10 bg-white/[0.025] p-1">
            <Link
              href="/"
              className="rounded-xl bg-white/10 px-4 py-2 text-sm text-white"
            >
              Dashboard
            </Link>

            <Link
              href="/reports"
              className="rounded-xl px-4 py-2 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
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

        {/* INTRO */}

        <div className="mb-6">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-cyan-400">
            Safety intelligence overview
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight">
            Identify where serious events could emerge.
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
            SIFSentinel combines learned NLP classification,
            precursor extraction, Life-Saving Rule mapping,
            semantic similarity and risk prioritization.
          </p>
        </div>

        {/* KPI CARDS */}

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <StatCard
            label="Reports analyzed"
            value={totalReports.toLocaleString()}
            description="Reports currently in the intelligence database"
            accent="bg-cyan-400/70"
          />

          <StatCard
            label="SIF signals"
            value={sifSignals.toLocaleString()}
            description={`${sifRate.toFixed(1)}% currently flagged by the SIF model`}
            accent="bg-yellow-400/70"
          />

          <StatCard
            label="High + Critical"
            value={high.toLocaleString()}
            description="Reports requiring elevated prioritization"
            accent="bg-orange-400/70"
          />

          <StatCard
            label="Critical"
            value={critical.toLocaleString()}
            description="Highest current precursor priority"
            accent="bg-red-400/70"
          />

        </section>

        {/* MAIN ANALYTICS */}

        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.25fr]">

          {/* RISK */}

          <Panel
            title="Risk Distribution"
            subtitle="Current precursor prioritization"
          >
            <div className="h-[280px]">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <PieChart>
                  <Pie
                    data={priorityDistribution}
                    dataKey="count"
                    nameKey="band"
                    innerRadius={72}
                    outerRadius={104}
                    paddingAngle={3}
                  >
                    {priorityDistribution.map(
                      (entry) => (
                        <Cell
                          key={entry.band}
                          fill={
                            entry.band === "Critical"
                              ? "#ef4444"
                              : entry.band === "High"
                              ? "#f97316"
                              : entry.band === "Moderate"
                              ? "#eab308"
                              : "#22c55e"
                          }
                        />
                      ),
                    )}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "#111111",
                      border:
                        "1px solid rgba(255,255,255,0.1)",
                      borderRadius: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {priorityDistribution.map(
                (item) => (
                  <div
                    key={item.band}
                    className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.025] px-4 py-3"
                  >
                    <span className="text-sm text-zinc-400">
                      {item.band}
                    </span>

                    <span className="font-mono text-sm text-white">
                      {item.count.toLocaleString()}
                    </span>
                  </div>
                ),
              )}
            </div>
          </Panel>

          {/* ACTIVITIES */}

          <Panel
            title="Top Activities"
            subtitle="Activities with the highest concentration of reports"
          >
            <div className="h-[350px]">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={activities}
                  layout="vertical"
                  margin={{
                    left: 8,
                    right: 12,
                    top: 4,
                    bottom: 4,
                  }}
                >
                  <CartesianGrid
                    stroke="rgba(255,255,255,0.06)"
                    horizontal={false}
                  />

                  <XAxis
                    type="number"
                    stroke="#71717a"
                    tickLine={false}
                    axisLine={false}
                  />

                  <YAxis
                    type="category"
                    dataKey="activity"
                    width={190}
                    stroke="#71717a"
                    tickLine={false}
                    axisLine={false}
                    tick={{
                      fill: "#a1a1aa",
                      fontSize: 11,
                    }}
                  />

                  <Tooltip
                    cursor={{
                      fill: "rgba(255,255,255,0.03)",
                    }}
                    contentStyle={{
                      background: "#111111",
                      border:
                        "1px solid rgba(255,255,255,0.1)",
                      borderRadius: 12,
                    }}
                  />

                  <Bar
                    dataKey="count"
                    fill="#22d3ee"
                    radius={[0, 6, 6, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>

        </section>

        {/* LIFE SAVING RULES */}

        <Panel
          title="IOGP Life-Saving Rules"
          subtitle="Rules most frequently associated with analyzed reports"
          className="mt-6"
        >
          <div className="grid gap-3 md:grid-cols-2">
            {lsr.map((item, index) => {

              const maxCount =
                lsr[0]?.count || 1;

              const percentage =
                Math.min(
                  100,
                  (item.count / maxCount) * 100,
                );

              return (
                <div
                  key={item.rule}
                  className="rounded-2xl border border-white/5 bg-white/[0.025] p-4"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="font-mono text-xs text-zinc-600">
                        {String(index + 1).padStart(2, "0")}
                      </span>

                      <span className="truncate text-sm text-zinc-200">
                        {item.rule}
                      </span>
                    </div>

                    <span className="shrink-0 font-mono text-sm text-white">
                      {item.count.toLocaleString()}
                    </span>
                  </div>

                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full bg-cyan-400 transition-all"
                      style={{
                        width: `${percentage}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        {/* PRIORITY REPORTS */}

        <Panel
          title="Highest-Priority Reports"
          subtitle="Reports currently ranked highest by the precursor risk engine"
          className="mt-6"
        >
          <div className="space-y-2">
            {priorityReports.map((report) => (
              <Link
                key={report.report_id}
                href={`/reports/${encodeURIComponent(
                  report.report_id,
                )}`}
                className="block rounded-2xl border border-white/5 bg-white/[0.02] p-4 transition hover:border-white/10 hover:bg-white/[0.045]"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-mono text-sm text-cyan-300">
                        {report.report_id}
                      </span>

                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs ${riskClass(
                          report.priority_band,
                        )}`}
                      >
                        {report.priority_band ?? "Unknown"}
                      </span>

                      <span className="text-xs text-zinc-600">
                        SIF {formatPercent(
                          report.sif_probability,
                        )}
                      </span>
                    </div>

                    <p className="mt-2 max-w-4xl truncate text-sm text-zinc-400">
                      {report.description}
                    </p>

                    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-600">
                      <span>
                        {report.activity ?? "Activity not detected"}
                      </span>

                      <span>•</span>

                      <span>
                        {report.location ?? "Location unavailable"}
                      </span>
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center gap-5">
                    <div className="text-right">
                      <p className="text-[10px] uppercase tracking-wider text-zinc-600">
                        Priority score
                      </p>

                      <p className="mt-1 font-mono text-sm text-white">
                        {report.priority_score !== null
                          ? report.priority_score.toFixed(3)
                          : "—"}
                      </p>
                    </div>

                    <span className="text-zinc-600 transition group-hover:text-white">
                      →
                    </span>
                  </div>

                </div>
              </Link>
            ))}
          </div>
        </Panel>



      </div>
    </main>
  );
}