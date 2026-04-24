# BU Course Planner Scaffold

This is a modular TypeScript monorepo scaffold for your EC327 BU Course Sequencing Tool project.

It includes:
- Express + TypeScript backend
- Prisma + PostgreSQL schema
- Email verification / password reset flow
- React + Vite frontend shell
- Planner modules for prerequisites, schedule generation, and Hub recommendations
- Public schedules, reviews, and comments modules

## Important security note
Passwords are **hashed with Argon2**. They are not reversibly encrypted.

## Apps
- `apps/server` — API server
- `apps/web` — React frontend
- `packages/shared` — shared types/utilities

## Quick start

```bash
npm install
cp .env.example .env
npm run prisma:generate
npm run prisma:migrate
npm run seed
npm run dev:server
npm run dev:web
```

## What is implemented
- modular backend routing and service layout
- auth registration/login/forgot/reset/verify flow
- database schema for users, courses, majors, schedules, reviews, comments
- starter planner services and frontend pages

## What still needs project-specific work
- import your real `bu_courses.json` offerings into `CourseOffering`
- import public catalog Hub areas into `Course` / `CourseHubArea`
- seed major requirements from your degree planning sheets
- refine prerequisite logic for OR groups / co-reqs
- harden schedule conflict detection and ranking
- finish frontend state management and UI polish

## Suggested implementation order
1. Stand up database and auth
2. Import course + offering data
3. Seed CE and ME major requirements
4. Build course builder UI
5. Build semester planner UI
6. Add public schedules and reviews
