import express from "express";
import { getTaxiAvailability } from "../controllers/taxiAvailability.controller.js";

const router = express.Router();

router.get("/top", getTaxiAvailability);

export default router;