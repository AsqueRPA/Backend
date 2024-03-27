import Bull from "bull";
import dotenv from "dotenv";
import { spawn } from "child_process";
import { Flow } from "../models/Flow.js";
import { Proxy } from "../models/Proxy.js";

dotenv.config();

const jobQueues = {};

const setup = async () => {
  const proxies = await Proxy.find({});
  proxies.forEach(
    (proxy) =>
      (jobQueues[proxy.account] = new Bull(`${proxy.account}-jobQueue`, {
        redis: {
          host: process.env.REDIS_HOST, // e.g., '127.0.0.1'
          port: process.env.REDIS_PORT, // e.g., 6379
        },
      }))
  );

  await Promise.all(
    proxies.map(async (proxy) => await jobQueues[proxy.account].empty())
  );

  proxies.forEach((proxy) => jobQueues[proxy.account].process(processJob));
};

const processJob = async (job) => {
  const {
    account,
    email,
    keyword,
    question,
    type,
    lastPage,
    targetAmountReachout,
    customized_message,
  } = job.data;
  const proxy = await Proxy.findOne({ account });
  proxy.isInUse = true;
  await proxy.save();
  if (type === "reachout") {
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn("python3.11", [
        "-u",
        "./generated_reachout.py",
        "-a",
        account,
        "-e",
        email,
        "-k",
        keyword,
        "-q",
        question,
        "-l",
        lastPage,
        "-t",
        targetAmountReachout,
        "-c",
        customized_message,
      ]);

      pythonProcess.stdout.on("data", (data) => {
        console.log(`stdout: ${data}`);
      });

      pythonProcess.stderr.on("data", (data) => {
        console.error(`stderr: ${data}`);
      });

      pythonProcess.on("close", async (code) => {
        proxy.isInUse = false;
        await proxy.save();
        if (code === 0) {
          resolve(`Process completed with code ${code}`);
        } else {
          reject(`Process failed with code ${code}`);
        }
      });
    });
  } else {
    const flow = await Flow.findOne({ account, email, keyword, question });
    return new Promise((resolve, reject) => {
      const pythonProcess = spawn("python3.11", [
        "-u",
        "./generated_reply.py",
        "-a",
        account,
        "-e",
        email,
        "-k",
        keyword,
        "-q",
        question,
        "-r",
        flow.reachouts
          .filter((reachout) => !reachout.response)
          .map((reachout) => reachout.name),
      ]);

      pythonProcess.stdout.on("data", (data) => {
        console.log(`stdout: ${data}`);
      });

      pythonProcess.stderr.on("data", (data) => {
        console.error(`stderr: ${data}`);
      });

      pythonProcess.on("close", async (code) => {
        proxy.isInUse = false;
        await proxy.save();
        if (code === 0) {
          resolve(`Process completed with code ${code}`);
        } else {
          reject(`Process failed with code ${code}`);
        }
      });
    });
  }
};

function scheduleReplyJob(account, email, keyword, question, delay) {
  jobQueues[account]
    .add(
      { account, email, keyword, question, type: "reply" },
      {
        delay: delay,
      }
    )
    .then((job) => {
      job
        .finished()
        .then(async () => {
          console.log(`Reply job ${job.id} completed`);
          const flow = await Flow.findOne({
            account,
            email,
            keyword,
            question,
          });
          // // this is to schedule another reachout if amount response is not met
          // // will be commented out first
          // if (
          //   flow.reachouts.filter((reachout) => reachout.response).length <
          //   flow.targetAmountResponse
          // ) {
          //   scheduleReachoutJob(
          //     account,
          //     email,
          //     keyword,
          //     question,
          //     flow.lastPage
          //   );
          // }
        })
        .catch((error) => {
          console.error(`Reply job ${job.id} failed`, error);
        });
    });
}

const HOURS = 3600000;

const TIME_BEFORE_CHECKING_REPLY = 12 * HOURS; // 12 hours

function scheduleReachoutJob(
  account,
  email,
  keyword,
  question,
  lastPage,
  targetAmountReachout,
  customized_message
) {
  jobQueues[account]
    .add({
      account,
      email,
      keyword,
      question,
      lastPage,
      targetAmountReachout,
      customized_message,
      type: "reachout",
    })
    .then((job) => {
      job
        .finished()
        .then(async () => {
          console.log(`Reachout job ${job.id} completed`);
          scheduleReplyJob(
            account,
            email,
            keyword,
            question,
            TIME_BEFORE_CHECKING_REPLY
          );
        })
        .catch((error) => {
          console.error(`Reachout job ${job.id} failed`, error);
        });
    });
}

export { scheduleReachoutJob, setup };
