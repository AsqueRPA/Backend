import { MongoClient } from "mongodb";
import mongoose from "mongoose";
import dotenv from "dotenv";
dotenv.config();

const connectDB = async () => {
  let db;
  if (process.env.NODE_ENV === "production") {
    db = process.env.DB;
  } else {
    db = process.env.DEV_DB;
  }
  
  await mongoose
    .connect(db)
    .then(() => {
      console.log("Connected to MongoDB...");
    })
    .catch((err) => console.log(err));
};

async function copyDatabase() {
  const uri = "bruh";
  const client = new MongoClient(uri, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  });

  try {
    await client.connect();

    // List of collections to copy
    const collections = await client.db("dev").listCollections().toArray();

    for (let collInfo of collections) {
      const collectionName = collInfo.name;
      const documents = await client
        .db("dev")
        .collection(collectionName)
        .find({})
        .toArray();

      // Inserting documents to the new database (dev_copy)
      if (documents.length > 0) {
        await client
          .db("prod")
          .collection(collectionName)
          .insertMany(documents);
      }
    }

    console.log("Database copied successfully.");
  } catch (err) {
    console.error(err);
  } finally {
    await client.close();
  }
}

export { connectDB };
