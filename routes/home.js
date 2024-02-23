import express from "express";
import dotenv from "dotenv";
import { Flow } from "../models/Flow.js";
import { jobQueue, scheduleReachoutJob } from "../utils/JobQueue.js";

dotenv.config();
const router = express.Router();

router.post("/reachout", async (req, res) => {
  try {
    const { account, email, keyword, question, targetAmountResponse } = req.body;
    let flow = await Flow.findOne({ account, email, keyword, question });
    if (flow === null) {
      flow = new Flow({
        account,
        email,
        keyword,
        question,
        targetAmountResponse,
        reachouts: [],
      });
      await flow.save();
    }
    scheduleReachoutJob(
      account,
      email,
      keyword,
      question,
      targetAmountResponse,
      flow.lastPage
    );
    return res.status(200).send("Reachout queued");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/record-reachout", async (req, res) => {
  try {
    const { account, email, keyword, question, name } = req.body;
    const flow = await Flow.findOne({ account, email, keyword, question });
    flow.reachouts.push({ name, response: "" });
    await flow.save();
    return res.status(200).send("Reachout recorded");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/delete-reachout", async (req, res) => {
  try {
    const { account, email, keyword, question, name } = req.body;
    const flow = await Flow.findOne({ account, email, keyword, question });
    flow.reachouts = flow.reachouts.filter(
      (reachout) => reachout.name !== name
    );
    await flow.save();
    return res.status(200).send("Reachout deleted");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/record-response", async (req, res) => {
  try {
    const { account, email, keyword, question, name, response } = req.body;
    const flow = await Flow.findOne({ account, email, keyword, question });
    flow.reachouts.map((reachout) => {
      if (reachout.name === name) {
        reachout.response = response;
      }
    });
    await flow.save();
    return res.status(200).send("Response recorded");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/amount-reachout", async (req, res) => {
  try {
    const { account, email, keyword, question } = req.body;
    const flow = await Flow.findOne({ account, email, keyword, question });
    return res
      .status(200)
      .send({ currentAmountReachout: flow.reachouts.length });
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/update-last-page", async (req, res) => {
  try {
    const { account, email, keyword, question, lastPage } = req.body;
    const flow = await Flow.findOne({ account, email, keyword, question });
    flow.lastPage = lastPage;
    await flow.save();
    return res.status(200).send("Last page updated");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.get("/jobs-queued", async (req, res) => {
  try {
    const jobs = await jobQueue.getJobs(["waiting", "delayed"]);
    return res.status(200).send({ jobsQueued: jobs.length });
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

export default router;
