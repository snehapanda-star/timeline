import pkg from "@prisma/client";

const { PrismaClient } = pkg as typeof import("@prisma/client");

const prisma = new PrismaClient();

async function main() {
  // Skills
  const skills = [
    { name: "Project Planning", description: "Break down goals into milestones and tasks." },
    { name: "Learning Strategy", description: "Choose effective learning methods and iterate." },
    { name: "Communication", description: "Document progress and ask for feedback." },
    { name: "Time Management", description: "Plan weekly work and track hours." },
  ];

  for (const s of skills) {
    await prisma.skill.upsert({
      where: { name: s.name },
      update: { description: s.description },
      create: s,
    });
  }

  // Badges
  const badges = [
    { name: "First Milestone", description: "Complete your first milestone." },
    { name: "Consistency Streak", description: "Maintain a learning streak." },
    { name: "Skill Builder", description: "Improve a skill level." },
  ];

  for (const b of badges) {
    await prisma.badge.upsert({
      where: { name: b.name },
      update: { description: b.description },
      create: b,
    });
  }

  // Optional: create a demo goal if no users exist.
  const userCount = await prisma.user.count();
  if (userCount === 0) {
    // No-op: auth user creation is handled by NextAuth.
    // Keeping seed safe for fresh environments.
  }

  // Create a sample recommendation template (no goalId) is not possible due to schema.
  // So we only seed global entities (skills, badges).
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
