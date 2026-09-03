"use client";

import Link from "next/link";
import {
  ChangeEvent,
  DragEvent,
  useEffect,
  useState,
} from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

type StepStatus =
  | "pending"
  | "running"
  | "complete"
  | "error";

type ProcessingStep = {
  name: string;
  stage: string;
  status: StepStatus;
};

type JobStatus = {
  dataset_id: string;
  dataset_name: string;
  filename: string;
  status: string;
  stage: string;
  progress: number;
  message: string | null;
  error: string | null;
};

const STEP_DEFINITIONS: ProcessingStep[] = [
  {
    name: "File received",
    stage: "upload",
    status: "pending",
  },
  {
    name: "Ingestion",
    stage: "ingestion",
    status: "pending",
  },
  {
    name: "Validation",
    stage: "validation",
    status: "pending",
  },
  {
    name: "Report loading",
    stage: "database",
    status: "pending",
  },
  {
    name: "SIF classification",
    stage: "sif_classification",
    status: "pending",
  },
  {
    name: "Precursor extraction",
    stage: "precursor_extraction",
    status: "pending",
  },
  {
    name: "LSR mapping",
    stage: "lsr_mapping",
    status: "pending",
  },
  {
    name: "Risk analysis",
    stage: "risk_analysis",
    status: "pending",
  },
  {
    name: "Embeddings",
    stage: "embeddings",
    status: "pending",
  },
];

function getStepStatuses(
  stage: string,
  status: string,
): ProcessingStep[] {
  if (status === "failed") {
    return STEP_DEFINITIONS.map((step) => {
      if (step.stage === stage) {
        return {
          ...step,
          status: "error",
        };
      }

      return step;
    });
  }

  if (status === "complete") {
    return STEP_DEFINITIONS.map((step) => ({
      ...step,
      status: "complete",
    }));
  }

  const stageOrder = STEP_DEFINITIONS.map(
    (step) => step.stage,
  );

  const currentIndex = stageOrder.indexOf(stage);

  return STEP_DEFINITIONS.map((step, index) => {
    if (currentIndex === -1) {
      return step;
    }

    if (index < currentIndex) {
      return {
        ...step,
        status: "complete",
      };
    }

    if (index === currentIndex) {
      return {
        ...step,
        status: "running",
      };
    }

    return {
      ...step,
      status: "pending",
    };
  });
}

function statusIcon(status: StepStatus) {
  switch (status) {
    case "complete":
      return (
        <span className="text-emerald-400">
          ✓
        </span>
      );

    case "running":
      return (
        <span className="animate-pulse text-cyan-400">
          ◌
        </span>
      );

    case "error":
      return (
        <span className="text-red-400">
          !
        </span>
      );

    default:
      return (
        <span className="text-zinc-600">
          ○
        </span>
      );
  }
}

function statusText(status: StepStatus) {
  switch (status) {
    case "complete":
      return "Complete";

    case "running":
      return "Running";

    case "error":
      return "Error";

    default:
      return "Pending";
  }
}

function formatProgress(progress: number) {
  return `${Math.max(
    0,
    Math.min(100, progress),
  )}%`;
}

export default function UploadPage() {
  const [file, setFile] =
    useState<File | null>(null);

  const [datasetName, setDatasetName] =
    useState("");

  const [dragging, setDragging] =
    useState(false);

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [datasetId, setDatasetId] =
    useState("");

  const [job, setJob] =
    useState<JobStatus | null>(null);

  const [steps, setSteps] =
    useState<ProcessingStep[]>(
      STEP_DEFINITIONS,
    );

  function selectFile(
    selectedFile: File | null,
  ) {
    setError("");
    setJob(null);
    setDatasetId("");
    setSteps(STEP_DEFINITIONS);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (
      !selectedFile.name
        .toLowerCase()
        .endsWith(".csv")
    ) {
      setError(
        "Please select a CSV file.",
      );
      setFile(null);
      return;
    }

    setFile(selectedFile);

    if (!datasetName) {
      const generatedName =
        selectedFile.name
          .replace(/\.csv$/i, "")
          .replace(/[_-]+/g, " ")
          .trim();

      setDatasetName(
        generatedName,
      );
    }
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    selectFile(
      event.target.files?.[0] ?? null,
    );
  }

  function handleDragOver(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setDragging(false);
  }

  function handleDrop(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setDragging(false);

    selectFile(
      event.dataTransfer.files?.[0] ??
        null,
    );
  }

  async function uploadReports() {
    setError("");

    if (!file) {
      setError(
        "Please select a CSV file first.",
      );
      return;
    }

    if (!datasetName.trim()) {
      setError(
        "Please enter a dataset name.",
      );
      return;
    }

    setUploading(true);
    setJob(null);
    setDatasetId("");

    setSteps(
      STEP_DEFINITIONS.map(
        (step, index) => ({
          ...step,
          status:
            index === 0
              ? "running"
              : "pending",
        }),
      ),
    );

    try {
      const formData =
        new FormData();

      formData.append(
        "file",
        file,
      );

      formData.append(
        "dataset_name",
        datasetName.trim(),
      );

      const response =
        await fetch(
          `${API_URL}/datasets/upload`,
          {
            method: "POST",
            body: formData,
          },
        );

      if (!response.ok) {
        let message =
          "Upload failed.";

        try {
          const data =
            await response.json();

          if (data?.detail) {
            message =
              String(data.detail);
          }
        } catch {
          // Keep default message.
        }

        throw new Error(
          message,
        );
      }

      const data =
        await response.json();

      const id = String(
        data.dataset_id ?? "",
      );

      if (!id) {
        throw new Error(
          "Upload succeeded but no dataset ID was returned.",
        );
      }

      setDatasetId(id);
      setUploading(false);

      setSteps(
        STEP_DEFINITIONS.map(
          (step, index) => ({
            ...step,
            status:
              index === 0
                ? "complete"
                : "pending",
          }),
        ),
      );
    } catch (uploadError) {
      setUploading(false);

      setSteps(
        STEP_DEFINITIONS.map(
          (step, index) => ({
            ...step,
            status:
              index === 0
                ? "error"
                : "pending",
          }),
        ),
      );

      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Upload failed.",
      );
    }
  }

  useEffect(() => {
    if (!datasetId) {
      return;
    }

    let cancelled = false;

    async function pollStatus() {
      try {
        const response =
          await fetch(
            `${API_URL}/datasets/${encodeURIComponent(
              datasetId,
            )}/status`,
            {
              cache: "no-store",
            },
          );

        if (!response.ok) {
          throw new Error(
            `Status request failed (${response.status}).`,
          );
        }

        const data =
          (await response.json()) as JobStatus;

        if (cancelled) {
          return;
        }

        setJob(data);

        setSteps(
          getStepStatuses(
            data.stage,
            data.status,
          ),
        );

        if (
          data.status ===
            "complete" ||
          data.status ===
            "failed"
        ) {
          return;
        }

        window.setTimeout(
          pollStatus,
          1500,
        );
      } catch (statusError) {
        if (cancelled) {
          return;
        }

        setError(
          statusError instanceof Error
            ? statusError.message
            : "Could not retrieve processing status.",
        );

        window.setTimeout(
          pollStatus,
          3000,
        );
      }
    }

    pollStatus();

    return () => {
      cancelled = true;
    };
  }, [datasetId]);

  const processing =
    Boolean(datasetId) &&
    job?.status !== "complete" &&
    job?.status !== "failed";

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
              className="rounded-xl px-4 py-2 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
            >
              Reports
            </Link>

            <Link
              href="/upload"
              className="rounded-xl bg-white/10 px-4 py-2 text-sm text-white"
            >
              Upload Report
            </Link>
          </nav>
        </header>

        {/* TITLE */}

        <div className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-cyan-400">
            Data ingestion
          </p>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight">
            Upload Reports
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Upload an OSHA-format CSV dataset and
            SIFSentinel will automatically analyze the
            reports for SIF signals, precursors,
            Life-Saving Rules, risk and semantic similarity.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">

          {/* UPLOAD */}

          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <div>
              <h3 className="text-base font-medium">
                Report Dataset
              </h3>

              <p className="mt-1 text-sm text-zinc-500">
                Select a CSV file to begin automated analysis.
              </p>
            </div>

            {/* DROP ZONE */}

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`mt-6 rounded-2xl border-2 border-dashed p-10 text-center transition ${
                dragging
                  ? "border-cyan-400 bg-cyan-400/10"
                  : "border-white/10 bg-black/20 hover:border-white/20"
              }`}
            >
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/10 text-2xl text-cyan-400">
                ↑
              </div>

              <h3 className="mt-5 text-lg font-medium">
                {file
                  ? file.name
                  : "Drop your CSV here"}
              </h3>

              <p className="mt-2 text-sm text-zinc-500">
                {file
                  ? `${(
                      file.size /
                      1024 /
                      1024
                    ).toFixed(2)} MB`
                  : "or choose a CSV from your computer"}
              </p>

              <label className="mt-6 inline-flex cursor-pointer items-center rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium transition hover:bg-white/10">
                Browse CSV

                <input
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={
                    handleFileChange
                  }
                  disabled={
                    uploading ||
                    processing
                  }
                />
              </label>
            </div>

            {/* DATASET NAME */}

            <div className="mt-6">
              <label
                htmlFor="dataset-name"
                className="mb-2 block text-sm font-medium text-zinc-300"
              >
                Dataset Name
              </label>

              <input
                id="dataset-name"
                type="text"
                value={datasetName}
                onChange={(event) =>
                  setDatasetName(
                    event.target.value,
                  )
                }
                placeholder="e.g. OSHA 2025 Incidents"
                disabled={
                  uploading ||
                  processing
                }
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/40 disabled:opacity-50"
              />
            </div>

            {/* ERROR */}

            {error && (
              <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}

            {/* JOB MESSAGE */}

            {job?.message && !error && (
              <div className="mt-5 rounded-xl border border-cyan-500/10 bg-cyan-500/[0.04] px-4 py-3 text-sm text-zinc-400">
                {job.message}
              </div>
            )}

            {/* ACTION */}

            <button
              type="button"
              onClick={uploadReports}
              disabled={
                uploading ||
                processing ||
                !file
              }
              className="mt-6 w-full rounded-xl bg-cyan-400 px-5 py-3.5 text-sm font-semibold text-black transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {uploading
                ? "Uploading..."
                : processing
                ? "Processing..."
                : "Upload & Analyze"}
            </button>

            {job?.status ===
              "complete" && (
              <Link
                href="/reports"
                className="mt-3 block w-full rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3.5 text-center text-sm text-zinc-300 transition hover:bg-white/[0.06] hover:text-white"
              >
                View analyzed reports →
              </Link>
            )}

          </section>

          {/* PROCESSING */}

          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-base font-medium">
                  Processing
                </h3>

                <p className="mt-1 text-sm text-zinc-500">
                  Automated intelligence pipeline
                </p>
              </div>

              {job && (
                <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-zinc-400">
                  {formatProgress(
                    job.progress,
                  )}
                </span>
              )}
            </div>

            {/* PROGRESS */}

            <div className="mt-6">
              <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    job?.status ===
                    "failed"
                      ? "bg-red-400"
                      : job?.status ===
                        "complete"
                      ? "bg-emerald-400"
                      : "bg-cyan-400"
                  }`}
                  style={{
                    width: `${Math.max(
                      0,
                      Math.min(
                        100,
                        job?.progress ?? 0,
                      ),
                    )}%`,
                  }}
                />
              </div>
            </div>

            {/* STEPS */}

            <div className="mt-6 space-y-1">
              {steps.map((step) => (
                <div
                  key={step.name}
                  className="flex items-center gap-4 rounded-xl px-3 py-3 transition hover:bg-white/[0.025]"
                >
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-black/30 text-sm">
                    {statusIcon(
                      step.status,
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-sm ${
                        step.status ===
                        "pending"
                          ? "text-zinc-600"
                          : "text-zinc-200"
                      }`}
                    >
                      {step.name}
                    </p>
                  </div>

                  <span className="text-xs text-zinc-600">
                    {statusText(
                      step.status,
                    )}
                  </span>
                </div>
              ))}
            </div>

            {/* CURRENT MESSAGE */}

            <div className="mt-6 rounded-2xl border border-white/5 bg-black/20 p-4">
              {job ? (
                <>
                  <p className="text-xs uppercase tracking-wider text-zinc-600">
                    Current status
                  </p>

                  <p className="mt-2 text-sm text-zinc-300">
                    {job.message ??
                      "Processing dataset..."}
                  </p>

                  {job.status ===
                    "failed" &&
                    job.error && (
                      <p className="mt-2 text-xs leading-5 text-red-300">
                        {job.error}
                      </p>
                    )}

                  {job.status ===
                    "complete" && (
                    <p className="mt-2 text-xs text-emerald-400">
                      Dataset processing complete.
                    </p>
                  )}
                </>
              ) : (
                <>
                  <p className="text-sm text-zinc-500">
                    Select a CSV file and upload it
                    to start automated analysis.
                  </p>
                </>
              )}
            </div>

          </section>
        </div>

        {/* AI PIPELINE */}

        <section className="mt-6 rounded-2xl border border-white/10 bg-white/[0.03] p-6">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-cyan-400">
              Automated analysis
            </p>

            <h3 className="mt-2 text-base font-medium">
              What happens after upload?
            </h3>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

            {[
              [
                "01",
                "SIF NLP",
                "Classifies report narratives for SIF precursor signals.",
              ],
              [
                "02",
                "Safety features",
                "Extracts activity, hazards, exposure and barrier failures.",
              ],
              [
                "03",
                "Life-Saving Rules",
                "Maps reports to the IOGP Life-Saving Rules.",
              ],
              [
                "04",
                "Semantic intelligence",
                "Creates embeddings for historical similarity search.",
              ],
            ].map(
              ([number, title, description]) => (
                <div
                  key={title}
                  className="rounded-2xl border border-white/5 bg-black/20 p-4"
                >
                  <span className="font-mono text-xs text-zinc-600">
                    {number}
                  </span>

                  <h4 className="mt-3 text-sm font-medium text-zinc-200">
                    {title}
                  </h4>

                  <p className="mt-2 text-xs leading-5 text-zinc-600">
                    {description}
                  </p>
                </div>
              ),
            )}

          </div>
        </section>

      </div>
    </main>
  );
}