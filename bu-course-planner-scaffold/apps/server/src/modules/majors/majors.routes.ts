import { Router } from "express";
import { majorsService } from "./majors.service";

export const majorsRouter = Router();

majorsRouter.get("/", async (_req, res) => {
  res.json(await majorsService.listMajors());
});

majorsRouter.get("/:code", async (req, res) => {
  res.json(await majorsService.getMajor(req.params.code));
});
