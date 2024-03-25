import express from "express";
import dotenv from "dotenv";
import { Flow } from "../models/Flow.js";
import { Proxy } from "../models/Proxy.js";
import { scheduleReachoutJob } from "../utils/JobQueue.js";
import {
  addToGoogleSheet,
  createAndShareSheet,
  givePermission,
  updateGoogleSheet,
} from "../utils/google_actions.js";

dotenv.config();
const router = express.Router();

router.post("/request-reachout", async (req, res) => {
  try {
    const { name, email, targetAudience, question, targetAmountResponse } = req.body;
    await addToGoogleSheet(
      [name, email, targetAudience, "", question, targetAmountResponse, "false"],
      "1iuv7C1jg5fmeFfcRakH_e9U2_0nkEP98pkqtHpy3Uaw"
    );

    return res.status(200).send("Reachout requested");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong.");
  }
});

router.post("/reachout", async (req, res) => {
  try {
    const { name, email, targetAudience, keyword, question, targetAmountResponse } = req.body;
    let randomProxy;
    let availableProxies = await Proxy.find({ isInUse: false });
    if (availableProxies.length) {
      randomProxy =
        availableProxies[Math.floor(Math.random() * availableProxies.length)];
    } else {
      randomProxy = (await Proxy.aggregate([{ $sample: { size: 1 } }]))[0];
    }

    let flow;
    let flows = await Flow.find({ name, email, targetAudience, keyword, question });
    let account;
    if (flows.length === 0) {
      // if this is the first flow created for this user's question

      // create spreadsheet and new flow
      const sheetName = `${name}'s SurveyBara`;

      const sheetId = await createAndShareSheet(
        sheetName,
        "hugozhan0802@gmail.com",
        question
      );

      account = randomProxy.account;

      flow = new Flow({
        account,
        name,
        email,
        targetAudience,
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
              $match: {
                _id: { $nin: proxiesUsed.map((proxy) => proxy._id) },
                isInUse: false,
              },
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
            targetAudience,
            sheetId: flows[0].sheetId,
            keyword,
            question,
            targetAmountResponse,
            reachouts: [],
          });
          await flow.save();
        }
      }
      account = availableProxy.account;
    }

    // schedule this flow to be ran
    scheduleReachoutJob(account, email, keyword, question, flow.lastPage);
    return res.status(200).send("Reachout queued");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/add-proxy", async (req, res) => {
  try {
    const { url, account, password } = req.body;
    let proxy = await Proxy.findOne({ url });
    if (proxy) {
      return res.status(400).send("Proxy already exists");
    }
    proxy = new Proxy({ url, account, password, isInUse: false });
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
    const responseCount = flow.reachouts.filter(
      (reachout) => reachout.response !== ""
    ).length;
    const masterSheetRowData = [
      name,
      email,
      flow.targetAudience,
      keyword,
      question,
      flow.targetAmountResponse,
      "true",
      flow.reachouts.length,
      responseCount,
      "https://docs.google.com/spreadsheets/d/" + flow.sheetId,
    ];
    await updateGoogleSheet(
      masterSheetRowData,
      "1iuv7C1jg5fmeFfcRakH_e9U2_0nkEP98pkqtHpy3Uaw"
    );
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
    const responseCount = flow.reachouts.filter(
      (reachout) => reachout.response !== ""
    ).length;

    if (!flow.sheetShared) {
      await givePermission(flow.sheetId, email);
      flow.sheetShared = true;
    }
    await flow.save();
    const sheetId = flow.sheetId;
    const userSheetRowData = [name, linkedinUrl, response];
    await addToGoogleSheet(userSheetRowData, sheetId);
    const masterSheetRowData = [
      name,
      email,
      flow.targetAudience,
      keyword,
      question,
      flow.targetAmountResponse,
      "true",
      flow.reachouts.length,
      responseCount,
      "https://docs.google.com/spreadsheets/d/" + flow.sheetId,
    ];
    await updateGoogleSheet(
      masterSheetRowData,
      "1iuv7C1jg5fmeFfcRakH_e9U2_0nkEP98pkqtHpy3Uaw"
    );
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

router.get("/get-proxy/:account", async (req, res) => {
  try {
    const { account } = req.params;
    const proxy = await Proxy.findOne({ account });
    return res.status(200).send({ proxy });
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

export default router;
