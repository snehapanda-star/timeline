import { NextResponse } from "next/server";

type Input = {
  goalTitle: string;
  goalDescription: string;
  weeklyHours: number;
  targetDate: string | null;
  constraints: string;
  skills: string[];
  qualities: string[];
  improveSkills: string[];
};

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function difficultyFromHours(hours: number) {
  if (hours >= 8) return "MEDIUM" as const;
  if (hours >= 4) return "MEDIUM" as const;
  return "HARD" as const;
}

export async function POST(req: Request) {
  const body = (await req.json()) as Input;

  const weeklyHours = clamp(Number(body.weeklyHours || 0), 1, 30);
  const improve = (body.improveSkills || []).slice(0, 6);
  const skills = (body.skills || []).slice(0, 6);
  const qualities = (body.qualities || []).slice(0, 6);

  // Simple duration heuristic: 10–24 weeks
  const baseWeeks = 12 + Math.round((6 - Math.min(6, skills.length)) * 2);
  const durationWeeks = clamp(baseWeeks, 10, 24);
  const phaseWeeks = Math.max(2, Math.round(durationWeeks / 3));

  const phases = [
    {
      title: "Foundation & Planning",
      objective: "Clarify scope, define success, and set up your learning workflow.",
      durationWeeks: phaseWeeks,
      difficulty: difficultyFromHours(weeklyHours),
      tasks: [
        {
          title: "Define the deliverable",
          estimatedHours: weeklyHours * 2,
          ideas: [
            "Write a 1-page spec: what ‘done’ looks like.",
            "List 5 must-have features/outputs.",
            "Create a checklist you can verify weekly.",
          ],
        },
        {
          title: "Build a learning loop",
          estimatedHours: weeklyHours * 2,
          ideas: [
            "Pick 1 resource per skill you want to improve.",
            "Schedule 2 focused sessions + 1 review session weekly.",
            "Track what you learned in 5 bullet points.",
          ],
        },
        {
          title: "Set up your practice environment",
          estimatedHours: weeklyHours * 1,
          ideas: [
            "Create a workspace/project folder.",
            "Prepare templates (notes, checklists, examples).",
            "Remove friction: bookmarks, shortcuts, starter files.",
          ],
        },
      ],
      successMetrics: [
        "A clear definition of done.",
        "A weekly schedule you can follow.",
        "At least 1 small prototype or sample output.",
      ],
    },
    {
      title: "Skill Building & Iteration",
      objective: "Close the biggest skill gaps through small, repeatable practice.",
      durationWeeks: phaseWeeks,
      difficulty: "MEDIUM" as const,
      tasks: improve.length
        ? improve.slice(0, 3).map((s, i) => ({
            title: `Practice: ${s}`,
            estimatedHours: weeklyHours * (2 + i),
            ideas: [
              `Do 3 short exercises for ${s} (not one long session).`,
              "Apply it immediately to your goal deliverable.",
              "Get feedback (peer, mentor, or self-review rubric).",
            ],
          }))
        : [
            {
              title: "Targeted practice",
              estimatedHours: weeklyHours * 3,
              ideas: [
                "Pick one sub-skill and practice for 45–60 minutes.",
                "Create a mini-output you can show.",
                "Repeat next week with a small variation.",
              ],
            },
          ],
      successMetrics: [
        "You can explain the skill gap in your own words.",
        "You produced 2–3 tangible improvements.",
        "Your process is faster than week 1.",
      ],
    },
    {
      title: "Integration & Completion",
      objective: "Combine everything into the final deliverable and polish it.",
      durationWeeks: durationWeeks - phaseWeeks * 2,
      difficulty: "EASY" as const,
      tasks: [
        {
          title: "Integrate core components",
          estimatedHours: weeklyHours * 3,
          ideas: [
            "Turn your checklist into a build order.",
            "Fix the top 3 blockers first.",
            "Do one ‘quality pass’ at the end.",
          ],
        },
        {
          title: "Polish & validate",
          estimatedHours: weeklyHours * 2,
          ideas: [
            "Create a rubric and score yourself.",
            "Test with a real user or a friend.",
            "Document what you learned for future goals.",
          ],
        },
        {
          title: "Ship",
          estimatedHours: weeklyHours * 1,
          ideas: [
            "Publish/share your final output.",
            "Write a short reflection: what worked, what didn’t.",
            "Plan the next iteration or next goal.",
          ],
        },
      ],
      successMetrics: [
        "Deliverable matches your definition of done.",
        "You can demonstrate it end-to-end.",
        "You have a repeatable process for the next goal.",
      ],
    },
  ];

  const skillGap = (improve.length ? improve : ["One key missing skill"]).map((s) => ({
    skill: s,
    whyItMatters: `Because it directly impacts your ability to complete “${body.goalTitle}”.`,
    improvementPlan: [
      `Break ${s} into 3 micro-skills and practice each for 1 week.`,
      "Use a rubric to self-check quality.",
      "Apply the micro-skill to your deliverable immediately.",
      `Leverage your strengths (${qualities.join(", ") || "consistency"}) to stay on schedule.`,
    ],
  }));

  const nextActions = [
    "Write your definition of done (5 bullet checklist).",
    "Pick 1 resource for each skill you want to improve.",
    "Schedule 2 focused sessions + 1 review session this week.",
    "Create a small prototype/output by the end of week 1.",
  ];

  const plan = {
    goalTitle: body.goalTitle,
    phases,
    skillGap,
    nextActions,
  };

  return NextResponse.json(plan);
}
