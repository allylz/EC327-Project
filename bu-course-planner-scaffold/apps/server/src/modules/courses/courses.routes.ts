import { Router } from "express";
import { coursesService } from "./courses.service";

export const coursesRouter = Router();

coursesRouter.get("/", async (req, res) => {
  res.json(await coursesService.listCourses(typeof req.query.search === "string" ? req.query.search : undefined));
});
