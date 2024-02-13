import express from "express";
import cors from "cors";
import bodyParser from "body-parser";
import { connectDB } from "./utils/db.js";
import dotenv from "dotenv";
dotenv.config();

// Connect to MongoDB database
(async () => await connectDB())();

const app = express();
app.use(cors());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Routers
import home from "./routes/home.js";

// middleware
app.use(express.json());

// Routes
app.use("/", home);

// Real IP Address
app.set("trust proxy", true);

const port = process.env.PORT || 80;
const server = app.listen(port, () => {
  console.log(`Listening on port ${port}...`);
});

process.on("SIGTERM", () => {
  server.close();
});

process.on("SIGINT", () => {
  server.close();
});

export default app;
