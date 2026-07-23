"use client";

import { useEffect, useState } from "react";

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

export default function TimelinePage() {
  const [plan, setPlan] = useState<TimelinePlan | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("goalpath_ai_plan");
    if (raw) {
      try {
        setPlan(JSON.parse(raw));
      } catch {
        // ignore
      }
    }
  }, []);

  if (!plan) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="text-2xl font-semibold">Timeline</h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
          No plan found yet. Go to the Goal Wizard to generate one.
        </p>
        <a
          href="/wizard"
          className="mt-4 inline-flex rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-black"
        >
          Open Goal Wizard
        </a>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Timeline</h1>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">{plan.goalTitle}</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
          <h2 className="font-semibold">Phases</h2>
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
                <div className="mt-3">
                  <p className="text-sm font-medium">Tasks</p>
                  <ul className="mt-2 space-y-2">
                    {p.tasks.map((t, i) => (
                      <li key={i} className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-black">
                        <div className="flex items-start justify-between gap-3">
                          <span className="text-sm font-medium">{t.title}</span>
                          <span className="text-xs text-zinc-500">~{t.estimatedHours}h</span>
                        </div>
                        <ul className="mt-2 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-200">
                          {t.ideas.slice(0, 3).map((idea, j) => (
                            <li key={j}>{idea}</li>
                          ))}
                        </ul>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="mt-3">
                  <p className="text-sm font-medium">Success metrics</p>
                  <ul className="mt-2 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-200">
                    {p.successMetrics.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside className="space-y-4">
          <section className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
            <h2 className="font-semibold">Skill gap</h2>
            <div className="mt-4 space-y-4">
              {plan.skillGap.map((s, idx) => (
                <div key={idx}>
                  <p className="font-medium">{s.skill}</p>
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">{s.whyItMatters}</p>
                  <ul className="mt-2 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-200">
                    {s.improvementPlan.slice(0, 4).map((x, i) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
            <h2 className="font-semibold">Next actions</h2>
            <ul className="mt-3 list-disc pl-5 text-sm text-zinc-700 dark:text-zinc-200">
              {plan.nextActions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </main>
  );
}
