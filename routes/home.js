import express from "express";
import dotenv from "dotenv";
import { Flow } from "../models/Flow.js";
import { Proxy } from "../models/Proxy.js";
import { jobQueue, scheduleReachoutJob } from "../utils/JobQueue.js";
import {
  createAndShareSheet,
  updateGoogleSheet,
} from "../utils/google_actions.js";

dotenv.config();
const router = express.Router();

router.post("/reachout", async (req, res) => {
  try {
    const { name, email, keyword, question, targetAmountResponse } = req.body;
    let randomProxy;
    let availableProxies = await Proxy.find({ isInUse: false });
    if (availableProxies.length) {
      randomProxy =
        availableProxies[Math.floor(Math.random() * availableProxies.length)];
    } else {
      randomProxy = (await Proxy.aggregate([{ $sample: { size: 1 } }]))[0];
    }

    let flow;
    let flows = await Flow.find({ name, email, keyword, question });
    if (flows.length === 0) {
      // if this is the first flow created for this user's question
      
      // create spreadsheet and new flow
      const sheetName = `${name}'s SurveyBara`;
      const sheetId = await createAndShareSheet(
        sheetName,
        email,
        question,
        targetAmountResponse
      );

      const account = randomProxy.account;

      flow = new Flow({
        account,
        name,
        email,
        sheetId,
        keyword,
        question,
        targetAmountResponse,
        reachouts: [],
      });
      await flow.save();
    } else {
      // if the user already has flows for this question
      let availableProxy;
      let proxiesUsed = [];

      // check if any of the existing flows can be ran right now
      for (const existingFlow of flows) {
        const proxy = await Proxy.findOne({ account: existingFlow.account });
        if (!proxy.isInUse) {
          availableProxy = proxy;
          flow = existingFlow;
          break;
        }
        proxiesUsed.push(proxy);
      }

      if (!availableProxy) {
        // if not then find and available proxy
        availableProxy = (
          await Proxy.aggregate([
            {
              $match: { _id: { $nin: proxiesUsed.map((proxy) => proxy._id) } },
            },
            { $sample: { size: 1 } },
          ])
        )[0];
        if (!availableProxy) {
          // if there is no available proxy then pick random from used
          const i = Math.floor(Math.random() * proxiesUsed.length);
          availableProxy = proxiesUsed[i];
          flow = flows[i];
        } else {
          // if there is then create new flow with new proxy
          flow = new Flow({
            account: availableProxy.account,
            name,
            email,
            sheetId: flows[0].sheetId,
            keyword,
            question,
            targetAmountResponse,
            reachouts: [],
          });
        }
      }
    }

    // schedule this flow to be ran
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

router.post("/add-proxy", async (req, res) => {
  try {
    const { url, account } = req.body;
    let proxy = await Proxy.findOne({ url });
    if (proxy) {
      return res.status(400).send("Proxy already exists");
    }
    proxy = new Proxy({ url, account });
    await proxy.save();
    return res.status(200).send("Proxy added");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/record-reachout", async (req, res) => {
  try {
    const { account, email, keyword, question, name, linkedinUrl } = req.body;
    const flow = await Flow.findOne({ account, email, keyword, question });
    flow.reachouts.push({ name, response: "", linkedinUrl });
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
    let linkedinUrl;
    flow.reachouts.map((reachout) => {
      if (reachout.name === name) {
        reachout.response = response;
        linkedinUrl = reachout.linkedinUrl;
      }
    });
    await flow.save();
    const sheetId = flow.sheetId;
    const rowData = [name, linkedinUrl, response]; //hugo how do we make sure response is good? so record-response route should be called after llm validate if the response is good?
    await updateGoogleSheet(rowData, sheetId);
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
    const jobs = await jobQueue.getJobs(["waiting", "delayed", "active"]);
    return res.status(200).send({ jobsQueued: jobs.length });
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

// router.post("/zapier-hook", async (req, res) => {
//   console.log('zapier has called this route')
//   try {
//     // Extract data from the request body
//     const { id, sheet_url } = req.body; // Adjust these fields based on what you're sending from Zapier
//     console.log('Data: ', req.body)

//     // Send a success response back to Zapier
//     res.status(200).json({ message: "Data received and recorded successfully" });

//     // Perform your database operation here
//     const flow = await Flow.findById(id);
//     if (!flow) {
//       return res.status(404).json({ message: "This outreach flow not found" });
//     }
//     flow.sheetUrl = sheet_url;
//     await flow.save();
//   } catch (error) {
//     console.error("Error saving data from Zapier:", error);
//     console.log("Error saving data from Zapier:", error);
//     res.status(500).json({ message: "Failed to record data" });
//   }
// });

export default router;
