"use client";

import { useMemo, useState } from "react";

type TimelinePhase = {
  title: string;
  objective: string;
  durationWeeks: number;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  tasks: { title: string; ideas: string[]; estimatedHours: number }[];
  successMetrics: string[];
};

type TimelinePlan = {
  goalTitle: string;
  phases: TimelinePhase[];
  skillGap: { skill: string; whyItMatters: string; improvementPlan: string[] }[];
  nextActions: string[];
};

function splitList(s: string) {
  return s
    .split(/\n|,/)
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function WizardPage() {
  const [goalTitle, setGoalTitle] = useState("Build a portfolio website");
  const [goalDescription, setGoalDescription] = useState(
    "Create a responsive portfolio with projects and a blog."
  );
  const [weeklyHours, setWeeklyHours] = useState(6);
  const [targetDate, setTargetDate] = useState("");
  const [constraints, setConstraints] = useState("Time is limited; prefer practical learning.");
  const [skills, setSkills] = useState("HTML/CSS, JavaScript basics");
  const [qualities, setQualities] = useState("Consistency, curiosity");
  const [improveSkills, setImproveSkills] = useState("React, UI/UX");

  const [plan, setPlan] = useState<TimelinePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const payload = useMemo(
    () => ({
      goalTitle,
      goalDescription,
      weeklyHours,
      targetDate: targetDate || null,
      constraints,
      skills: splitList(skills),
      qualities: splitList(qualities),
      improveSkills: splitList(improveSkills),
    }),
    [
      goalTitle,
      goalDescription,
      weeklyHours,
      targetDate,
      constraints,
      skills,
      qualities,
      improveSkills,
    ]
  );

  async function onGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/generate-timeline", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as TimelinePlan;
      setPlan(data);
      // Persist for Timeline page
      localStorage.setItem("goalpath_ai_plan", JSON.stringify(data));
    } catch (e: any) {
      setError(e?.message ?? "Failed to generate timeline");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Goal Wizard</h1>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
        Enter your goal and current skills. We’ll generate a simple, actionable timeline.
      </p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Goal title</span>
          <input
            className="rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={goalTitle}
            onChange={(e) => setGoalTitle(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Weekly availability (hours)</span>
          <input
            type="number"
            min={1}
            className="rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={weeklyHours}
            onChange={(e) => setWeeklyHours(Number(e.target.value))}
          />
        </label>

        <label className="flex flex-col gap-1 md:col-span-2">
          <span className="text-sm font-medium">Goal description</span>
          <textarea
            className="min-h-[110px] rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={goalDescription}
            onChange={(e) => setGoalDescription(e.target.value)}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Target completion date (optional)</span>
          <input
            type="date"
            className="rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={targetDate}
            onChange={(e) => setTargetDate(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Constraints / obstacles</span>
          <input
            className="rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={constraints}
            onChange={(e) => setConstraints(e.target.value)}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Skills you already have</span>
          <textarea
            className="min-h-[90px] rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
          />
          <span className="text-xs text-zinc-500">Comma or newline separated</span>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Strengths / qualities</span>
          <textarea
            className="min-h-[90px] rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={qualities}
            onChange={(e) => setQualities(e.target.value)}
          />
          <span className="text-xs text-zinc-500">Comma or newline separated</span>
        </label>

        <label className="flex flex-col gap-1 md:col-span-2">
          <span className="text-sm font-medium">Skills you want to improve</span>
          <textarea
            className="min-h-[90px] rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-black"
            value={improveSkills}
            onChange={(e) => setImproveSkills(e.target.value)}
          />
          <span className="text-xs text-zinc-500">Comma or newline separated</span>
        </label>
      </div>

      <div className="mt-6 flex items-center gap-3">
        <button
          onClick={onGenerate}
          disabled={loading}
          className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-zinc-100 dark:text-black"
        >
          {loading ? "Generating…" : "Generate timeline"}
        </button>
        <a
          href="/timeline"
          className="text-sm font-medium text-zinc-700 dark:text-zinc-200"
        >
          View timeline
        </a>
      </div>

      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

      {plan ? (
        <section className="mt-8 rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
          <h2 className="text-lg font-semibold">Preview</h2>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">{plan.goalTitle}</p>
          <div className="mt-4 space-y-4">
            {plan.phases.map((p, idx) => (
              <div key={idx} className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-900/40">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-medium">{p.title}</h3>
                    <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">{p.objective}</p>
                  </div>
                  <div className="text-right text-xs text-zinc-500">
                    {p.durationWeeks} weeks · {p.difficulty}
                  </div>
                </div>
                <ul className="mt-3 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-200">
                  {p.tasks.slice(0, 3).map((t, i) => (
                    <li key={i}>
                      <span className="font-medium">{t.title}</span> — {t.estimatedHours}h
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
