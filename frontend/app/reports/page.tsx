"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Report = {
  report_id: string;
  description: string;
  event_date?: string | null;
  employer?: string | null;
  city?: string | null;
  state?: string | null;
  sif_probability?: number | null;
  sif_label?: string | null;
  activity?: string | null;
  hazard?: string | null;
  life_saving_rules?: string[];
  priority_score?: number | null;
  priority_band?: string | null;
};

type ReportsResponse = {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  reports: Report[];
};

const PAGE_SIZE = 25;

const LSR_OPTIONS = [
  "Bypassing Safety Controls",
  "Confined Space",
  "Driving",
  "Energy Isolation",
  "Hot Work",
  "Line of Fire",
  "Safe Mechanical Lifting",
  "Work Authorisation",
  "Working at Height",
];

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

function sifClass(label: string | null | undefined) {
  if (label === "YES") {
    return "border-yellow-500/20 bg-yellow-500/10 text-yellow-300";
  }

  return "border-zinc-500/20 bg-zinc-500/10 text-zinc-400";
}

function formatDate(value?: string | null) {
  if (!value) {
    return "Unknown date";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);

  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");
  const [sifFilter, setSifFilter] = useState("All");
  const [lsrFilter, setLsrFilter] = useState("All");

  const [page, setPage] = useState(1);

  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  // ---------------------------------------------------------
  // LOAD REPORTS FROM BACKEND
  // ---------------------------------------------------------

  useEffect(() => {
    const timer = setTimeout(() => {
      async function loadReports() {
        try {
          setLoading(true);
          setError("");

          const params = new URLSearchParams();

          params.set("page", String(page));
          params.set("page_size", String(PAGE_SIZE));

          if (search.trim()) {
            params.set("search", search.trim());
          }

          if (riskFilter !== "All") {
            params.set("risk", riskFilter);
          }

          if (sifFilter !== "All") {
            params.set("sif", sifFilter);
          }

          if (lsrFilter !== "All") {
            params.set("lsr", lsrFilter);
          }

          const response = await fetch(
            `http://localhost:8000/reports?${params.toString()}`,
            {
              cache: "no-store",
            },
          );

          if (!response.ok) {
            throw new Error(
              `Failed to load reports (${response.status})`,
            );
          }

          const data: ReportsResponse = await response.json();

          setReports(data.reports);
          setTotal(data.total);
          setTotalPages(data.total_pages);
        } catch (err) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load reports.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadReports();
    }, 250);

    return () => clearTimeout(timer);
  }, [page, search, riskFilter, sifFilter, lsrFilter]);

  // ---------------------------------------------------------
  // RESET TO PAGE 1 WHEN FILTERS CHANGE
  // ---------------------------------------------------------

  useEffect(() => {
    setPage(1);
  }, [search, riskFilter, sifFilter, lsrFilter]);

  // ---------------------------------------------------------
  // PAGE BUTTONS
  // ---------------------------------------------------------

  const pageButtons = useMemo(() => {
    const pages: number[] = [];

    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);

    for (let current = start; current <= end; current += 1) {
      pages.push(current);
    }

    return pages;
  }, [page, totalPages]);

  const startRecord =
    total === 0
      ? 0
      : (page - 1) * PAGE_SIZE + 1;

  const endRecord = Math.min(
    page * PAGE_SIZE,
    total,
  );

  function clearFilters() {
    setSearch("");
    setRiskFilter("All");
    setSifFilter("All");
    setLsrFilter("All");
    setPage(1);
  }

  async function downloadReports() {
    try {
      setDownloading(true);

      const params = new URLSearchParams();

      if (search.trim()) {
        params.set("search", search.trim());
      }

      if (riskFilter !== "All") {
        params.set("risk", riskFilter);
      }

      if (sifFilter !== "All") {
        params.set("sif", sifFilter);
      }

      if (lsrFilter !== "All") {
        params.set("lsr", lsrFilter);
      }

      const queryString = params.toString();

      const response = await fetch(
        `http://localhost:8000/reports/export${
          queryString ? `?${queryString}` : ""
        }`,
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(
          `Failed to export reports (${response.status})`,
        );
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = "analysed_reports.csv";

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not download reports.",
      );
    } finally {
      setDownloading(false);
    }
  }

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

        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-cyan-400">
              Report intelligence
            </p>

            <h2 className="mt-2 text-3xl font-semibold tracking-tight">
              Reports
            </h2>

            <p className="mt-2 text-sm text-zinc-500">
              Search and investigate analyzed incident reports.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={downloadReports}
              disabled={downloading || total === 0}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {downloading
                ? "Downloading..."
                : "↓ Download Analysed Reports"}
            </button>

            <Link
              href="/upload"
              className="w-fit rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-black transition hover:bg-zinc-200"
            >
              Upload Report
            </Link>
          </div>
        </div>

        {/* SEARCH + FILTERS */}

        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <input
            type="text"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search report ID, narrative, employer, location, hazard..."
            className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3.5 text-sm text-white outline-none placeholder:text-zinc-600 transition focus:border-cyan-400/30"
          />

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <select
              value={riskFilter}
              onChange={(event) => {
                setRiskFilter(event.target.value);
                setPage(1);
              }}
              className="rounded-xl border border-white/10 bg-[#111111] px-3 py-3 text-sm text-zinc-300 outline-none"
            >
              <option value="All">All risk levels</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Moderate">Moderate</option>
              <option value="Low">Low</option>
            </select>

            <select
              value={sifFilter}
              onChange={(event) => {
                setSifFilter(event.target.value);
                setPage(1);
              }}
              className="rounded-xl border border-white/10 bg-[#111111] px-3 py-3 text-sm text-zinc-300 outline-none"
            >
              <option value="All">All SIF signals</option>
              <option value="YES">SIF signal — YES</option>
              <option value="NO">SIF signal — NO</option>
            </select>

            <select
              value={lsrFilter}
              onChange={(event) => {
                setLsrFilter(event.target.value);
                setPage(1);
              }}
              className="rounded-xl border border-white/10 bg-[#111111] px-3 py-3 text-sm text-zinc-300 outline-none"
            >
              <option value="All">
                All Life-Saving Rules
              </option>

              {LSR_OPTIONS.map((rule) => (
                <option key={rule} value={rule}>
                  {rule}
                </option>
              ))}
            </select>
          </div>
        </section>

        {/* RESULT SUMMARY */}

        <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-zinc-500">
            {loading
              ? "Loading reports..."
              : total === 0
                ? "No matching reports"
                : `Showing ${startRecord.toLocaleString()}–${endRecord.toLocaleString()} of ${total.toLocaleString()} reports`}
          </p>

          {!loading && total > 0 && (
            <p className="text-xs text-zinc-600">
              Page {page} of {totalPages}
            </p>
          )}
        </div>

        {/* ERROR */}

        {error && (
          <div className="mt-5 rounded-2xl border border-red-500/20 bg-red-500/5 p-5 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* LOADING */}

        {loading && !error && (
          <div className="mt-5 space-y-2">
            {[1, 2, 3, 4, 5].map((item) => (
              <div
                key={item}
                className="h-32 animate-pulse rounded-2xl border border-white/10 bg-white/[0.03]"
              />
            ))}
          </div>
        )}

        {/* EMPTY */}

        {!loading && !error && reports.length === 0 && (
          <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.03] p-10 text-center">
            <p className="text-sm text-zinc-400">
              No reports match the selected filters.
            </p>

            <button
              onClick={clearFilters}
              className="mt-3 text-sm text-cyan-400 hover:text-cyan-300"
            >
              Clear filters
            </button>
          </div>
        )}

        {/* REPORT LIST */}

        {!loading && !error && reports.length > 0 && (
          <section className="mt-5 space-y-2">
            {reports.map((report) => {
              const rules = report.life_saving_rules ?? [];

              return (
                <Link
                  key={report.report_id}
                  href={`/reports/${encodeURIComponent(report.report_id)}`}
                  className="group block rounded-2xl border border-white/10 bg-white/[0.025] p-5 transition hover:border-cyan-400/20 hover:bg-white/[0.04]"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-cyan-400">
                          {report.report_id}
                        </span>

                        {report.priority_band && (
                          <span
                            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium ${riskClass(report.priority_band)}`}
                          >
                            {report.priority_band}
                          </span>
                        )}

                        {report.sif_label && (
                          <span
                            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium ${sifClass(report.sif_label)}`}
                          >
                            SIF {report.sif_label}
                          </span>
                        )}
                      </div>

                      <h3 className="mt-3 line-clamp-2 text-sm font-medium leading-6 text-zinc-200 group-hover:text-white">
                        {report.description}
                      </h3>

                      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-zinc-500">
                        <span>
                          {formatDate(report.event_date)}
                        </span>

                        {report.employer && (
                          <span>{report.employer}</span>
                        )}

                        {(report.city || report.state) && (
                          <span>
                            {[report.city, report.state]
                              .filter(Boolean)
                              .join(", ")}
                          </span>
                        )}

                        {report.activity && (
                          <span>
                            Activity: {report.activity}
                          </span>
                        )}
                      </div>

                      {report.hazard && (
                        <p className="mt-3 text-xs text-zinc-600">
                          Hazard: {report.hazard}
                        </p>
                      )}

                      {rules.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {rules.slice(0, 4).map((rule) => (
                            <span
                              key={rule}
                              className="rounded-lg border border-white/10 bg-black/20 px-2.5 py-1 text-[11px] text-zinc-400"
                            >
                              {rule}
                            </span>
                          ))}

                          {rules.length > 4 && (
                            <span className="rounded-lg border border-white/10 bg-black/20 px-2.5 py-1 text-[11px] text-zinc-600">
                              +{rules.length - 4} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex shrink-0 items-center gap-8 lg:pl-6">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.16em] text-zinc-600">
                          SIF signal
                        </p>

                        <p className="mt-1 text-sm font-medium text-zinc-300">
                          {formatPercent(
                            report.sif_probability,
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-[0.16em] text-zinc-600">
                          Priority
                        </p>

                        <p className="mt-1 text-sm font-medium text-zinc-300">
                          {report.priority_score !== null &&
                          report.priority_score !== undefined
                            ? report.priority_score.toFixed(1)
                            : "—"}
                        </p>
                      </div>

                      <div className="text-zinc-600 transition group-hover:translate-x-0.5 group-hover:text-cyan-400">
                        →
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </section>
        )}

        {/* PAGINATION */}

        {!loading && !error && totalPages > 1 && (
          <div className="mt-7 flex flex-wrap items-center justify-center gap-2">
            <button
              disabled={page === 1}
              onClick={() =>
                setPage((current) => Math.max(1, current - 1))
              }
              className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-zinc-400 transition hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
            >
              Previous
            </button>

            {pageButtons.map((pageNumber) => (
              <button
                key={pageNumber}
                onClick={() => setPage(pageNumber)}
                className={`h-9 min-w-9 rounded-xl border px-3 text-sm transition ${
                  pageNumber === page
                    ? "border-cyan-400/20 bg-cyan-400/10 text-cyan-300"
                    : "border-white/10 bg-white/[0.03] text-zinc-400 hover:bg-white/[0.06] hover:text-white"
                }`}
              >
                {pageNumber}
              </button>
            ))}

            <button
              disabled={page === totalPages}
              onClick={() =>
                setPage((current) =>
                  Math.min(totalPages, current + 1),
                )
              }
              className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-zinc-400 transition hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
            >
              Next
            </button>
          </div>
        )}

        {/* FOOTER NOTE */}

        <div className="mt-10 border-t border-white/10 pt-5">
          <p className="text-xs leading-5 text-zinc-600">
            SIF probability is a model-generated ranking signal,
            not a calibrated probability of serious injury or
            fatality. Review findings in operational context before
            making safety decisions.
          </p>
        </div>
      </div>
    </main>
  );
}