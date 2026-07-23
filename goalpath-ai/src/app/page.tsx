import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white dark:bg-black text-zinc-900 dark:text-zinc-50">
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">GoalPath AI</h1>
            <p className="mt-2 text-zinc-600 dark:text-zinc-300">
              Generate a personalized timeline, milestones, and next actions.
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/wizard"
              className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-black"
            >
              Goal Wizard
            </Link>
            <Link
              href="/timeline"
              className="rounded-full border border-zinc-200 px-4 py-2 text-sm font-medium dark:border-zinc-800"
            >
              Timeline
            </Link>
          </div>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
            <h2 className="font-medium">1) Describe your goal</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              Title, description, constraints, and target date.
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
            <h2 className="font-medium">2) Share your skills</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              Current skills/qualities and what you want to improve.
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
            <h2 className="font-medium">3) Get a timeline</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              Phases, milestones, tasks, and a simple coaching chat.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
