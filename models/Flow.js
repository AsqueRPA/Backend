import mongoose from "mongoose";

const FlowSchema = new mongoose.Schema({
  /**************************************************************************
   *                             Flow Information                           *
   **************************************************************************/
  account: {
    type: String,
    required: true,
  },
  email: {
    type: String,
    required: true,
  },
  keyword: {
    type: String,
    required: true,
  },
  question: {
    type: String,
    required: true,
  },
  targetAmountResponse: {
    type: Number,
    default: 10,
  },
  lastPage: {
    type: Number,
    default: 0,
  },
  reachouts: [
    {
      name: {
        type: String,
        required: true,
      },
      response: {
        type: String,
      },
    },
  ],
});

export const Flow = mongoose.model("Flow", FlowSchema);
