import Bull from "bull";
import dotenv from "dotenv";
import { spawn } from "child_process";
import { Flow } from "../models/Flow.js";

dotenv.config();

const jobQueue = new Bull("jobQueue", {
  redis: {
    host: process.env.REDIS_HOST, // e.g., '127.0.0.1'
    port: process.env.REDIS_PORT, // e.g., 6379
  },
});
await jobQueue.empty();

jobQueue.process(async (job) => {
  const { account, email, keyword, question, type, targetAmountResponse, lastPage } = job.data;
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
        "-t",
        targetAmountResponse,
        "-l",
        lastPage,
      ]);

      pythonProcess.stdout.on("data", (data) => {
        console.log(`stdout: ${data}`);
      });

      pythonProcess.stderr.on("data", (data) => {
        console.error(`stderr: ${data}`);
      });

      pythonProcess.on("close", (code) => {
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

      pythonProcess.on("close", (code) => {
        if (code === 0) {
          resolve(`Process completed with code ${code}`);
        } else {
          reject(`Process failed with code ${code}`);
        }
      });
    });
  }
});

function scheduleReplyJob(account, email, keyword, question, delay) {
  jobQueue
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
          const flow = await Flow.findOne({ email, keyword, question });
          if (
            flow.reachouts.filter((reachout) => reachout.response).length <
            flow.targetAmountResponse
          ) {
            scheduleReachoutJob(email, keyword, question, flow.targetAmountResponse, flow.lastPage);
          }
        })
        .catch((error) => {
          console.error(`Reply job ${job.id} failed`, error);
        });
    });
}

function scheduleReachoutJob(account, email, keyword, question, targetAmountResponse, lastPage) {
  jobQueue
    .add({ account, email, keyword, question, targetAmountResponse, lastPage, type: "reachout" })
    .then((job) => {
      job
        .finished()
        .then(async () => {
          console.log(`Reachout job ${job.id} completed`);
          scheduleReplyJob(email, keyword, question, 3000);
        })
        .catch((error) => {
          console.error(`Reachout job ${job.id} failed`, error);
        });
    });
}

export { scheduleReachoutJob, jobQueue };
