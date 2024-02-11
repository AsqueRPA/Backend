import express from "express";
import dotenv from "dotenv";
import { spawn } from "child_process";

dotenv.config();

const router = express.Router();

router.post("/", async (req, res) => {
  try {
    const { keyword } = req.body;
    const pythonProcess = spawn("python3.11", [
      "./web_agent.py",
      "-p",
      keyword,
    ]);

    pythonProcess.stdout.on("data", (data) => {
      console.log(`stdout: ${data}`);
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error(`stderr: ${data}`);
    });

    pythonProcess.on("close", (code) => {
      console.log(`Process exited with code ${code}`);
    });

    return res.status(200).send("Process is running");
  } catch (error) {
    console.log(error);
    return res.status(400).send("Something went wrong");
  }
});

export default router;
