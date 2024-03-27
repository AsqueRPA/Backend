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
    const { name, email, targetAudience, question, targetAmountResponse } =
      req.body;
    await addToGoogleSheet(
      [
        name,
        email,
        targetAudience,
        question,
        "",
        targetAmountResponse,
        "false",
      ],
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
    const {
      name,
      email,
      targetAudience,
      keyword,
      question,
      targetAmountResponse,
      targetAmountReachout,
      customized_message,
    } = req.body;
    let randomProxy;
    let availableProxies = await Proxy.find({ isInUse: false });
    if (availableProxies.length) {
      randomProxy =
        availableProxies[Math.floor(Math.random() * availableProxies.length)];
    } else {
      randomProxy = (await Proxy.aggregate([{ $sample: { size: 1 } }]))[0];
    }

    let flow;
    // search to see if there are existing flows for the user's question
    let flows = await Flow.find({
      name,
      email,
      targetAudience,
      targetAmountResponse,
      question,
    });
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
      // search to see if there are existing flows with this keyword
      let keywordFlows = await Flow.find({
        name,
        email,
        targetAudience,
        keyword,
        targetAmountResponse,
        question,
      });

      if (keywordFlows.length === 0) {
        // if the user doesn't have any flows with this keyword
        account = randomProxy.account;
        // create new flow with the same spreadsheet
        flow = new Flow({
          account,
          name,
          email,
          targetAudience,
          sheetId: flows[0].sheetId,
          keyword,
          question,
          targetAmountResponse,
          reachouts: [],
        });
      } else {
        // if the user already has flows for this question and keyword
        let availableProxy;
        let proxiesUsed = [];

        // check if any of the existing flows can be ran right now
        for (const existingFlow of flows) {
          const proxy = await Proxy.findOne({ account: existingFlow.account });
          if (!proxy.isInUse) {
            availableProxy = proxy;
            account = availableProxy.account;
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
            account = availableProxy.account;
            flow = flows[i];
          } else {
            account = availableProxy.account;
            // if there is then create new flow with new proxy
            flow = new Flow({
              account,
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
      }
    }

    // schedule this flow to be ran
    scheduleReachoutJob(
      account,
      email,
      keyword,
      question,
      flow.lastPage,
      targetAmountReachout,
      customized_message,
    );
    return res.status(200).send("Reachout queued");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

router.post("/adjust-last-page", async (req, res) => {
  try {
    const {
      name,
      account,
      email,
      targetAudience,
      keyword,
      question,
      newLastPage,
    } = req.body;
    const flow = await Flow.findOne({
      name,
      account,
      email,
      targetAudience,
      keyword,
      question,
    });
    flow.lastPage = newLastPage;
    await flow.save();
    return res.status(200).send("Flow last page adjusted");
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
    await flow.save();
    const allFlows = await Flow.find({
      name: flow.name,
      email,
      targetAudience: flow.targetAudience,
      question,
      targetAmountResponse: flow.targetAmountResponse,
    });
    
    let allResponseCount = 0;
    let allReachoutCount = 0;
    allFlows.forEach((flow) => {
      const responseCount = flow.reachouts.filter(
        (reachout) => reachout.response !== ""
      ).length;
      allResponseCount += responseCount;
      allReachoutCount += flow.reachouts.length;
    });

    const masterSheetRowData = [
      flow.name,
      email,
      flow.targetAudience,
      question,
      keyword,
      flow.targetAmountResponse,
      "true",
      allReachoutCount,
      allResponseCount,
      "https://docs.google.com/spreadsheets/d/" + flow.sheetId,
    ];
    await updateGoogleSheet(
      masterSheetRowData,
      "1iuv7C1jg5fmeFfcRakH_e9U2_0nkEP98pkqtHpy3Uaw"
    );
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
    if (!flow.sheetShared) {
      await givePermission(flow.sheetId, email);
      flow.sheetShared = true;
    }
    await flow.save();

    const allFlows = await Flow.find({
      name: flow.name,
      email,
      targetAudience: flow.targetAudience,
      question,
      targetAmountResponse: flow.targetAmountResponse,
    });
    
    let allResponseCount = 0;
    let allReachoutCount = 0;
    allFlows.forEach((flow) => {
      const responseCount = flow.reachouts.filter(
        (reachout) => reachout.response !== ""
      ).length;
      allResponseCount += responseCount;
      allReachoutCount += flow.reachouts.length;
    });

    const sheetId = flow.sheetId;
    const userSheetRowData = [name, linkedinUrl, response];
    await addToGoogleSheet(userSheetRowData, sheetId);
    const masterSheetRowData = [
      flow.name,
      email,
      flow.targetAudience,
      question,
      keyword,
      flow.targetAmountResponse,
      "true",
      allReachoutCount,
      allResponseCount,
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
