import Bull from "bull";
import dotenv from "dotenv";
import { spawn } from "child_process";

dotenv.config();

const jobQueue = new Bull("attainJobQueue", {
  redis: {
    host: process.env.REDIS_HOST, // e.g., '127.0.0.1'
    port: process.env.REDIS_PORT, // e.g., 6379
  },
});
await jobQueue.empty();

jobQueue.process(async (job) => {
  const { filePath, username, password, type } = job.data;
  switch (type) {
    case "fritolay": {
      return new Promise((resolve, reject) => {
        const pythonProcess = spawn("python3.11", [
          "-u",
          "./fritolay_bot.py",
          "-f",
          filePath,
          "-u",
          username,
          "-p",
          password,
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
    default: {
      return;
    }
  }
});

function scheduleFritoLayJob(filePath, username, password) {
  jobQueue
    .add({ filePath, username, password, type: "fritolay" })
    .then((job) => {
      job
        .finished()
        .then(async () => {
          console.log(`FritoLay job ${job.id} completed`);
        })
        .catch((error) => {
          console.error(`FritoLay job ${job.id} failed`, error);
        });
    });
}

export { scheduleFritoLayJob, jobQueue };
