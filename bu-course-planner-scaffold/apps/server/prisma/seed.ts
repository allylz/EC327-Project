import "dotenv/config";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function seedHubAreas() {
  const hubAreas = [
    ["PLM", "Philosophical Inquiry and Life's Meanings"],
    ["AEX", "Aesthetic Exploration"],
    ["HCO", "Historical Consciousness"],
    ["SO", "Social Inquiry"],
    ["IIC", "Individual in Community"],
    ["GCI", "Global Citizenship and Intercultural Literacy"],
    ["ETR", "Ethical Reasoning"],
    ["QR1", "Quantitative Reasoning I"],
    ["QR2", "Quantitative Reasoning II"],
    ["SI1", "Scientific Inquiry I"],
    ["SI2", "Scientific Inquiry II"],
    ["FYW", "First-Year Writing Seminar"],
    ["WRI", "Writing, Research, and Inquiry"],
    ["WIN", "Writing-Intensive Course"],
    ["OSC", "Oral and/or Signed Communication"],
    ["DME", "Digital/Multimedia Expression"],
    ["CRT", "Critical Thinking"],
    ["RIL", "Research and Information Literacy"],
    ["TWC", "Teamwork/Collaboration"],
    ["CRI", "Creativity/Innovation"]
  ] as const;

  for (const [code, label] of hubAreas) {
    await prisma.hubArea.upsert({
      where: { code },
      update: { label },
      create: { code, label }
    });
  }
}

async function seedMajors() {
  await prisma.major.upsert({ where: { code: "CE" }, update: {}, create: { code: "CE", name: "Computer Engineering" } });
  await prisma.major.upsert({ where: { code: "ME" }, update: {}, create: { code: "ME", name: "Mechanical Engineering" } });
}

async function main() {
  await seedHubAreas();
  await seedMajors();
  console.log("Seeded hub areas and majors.");
}

main()
  .finally(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
