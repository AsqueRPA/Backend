import mongoose from "mongoose";

const ProxySchema = new mongoose.Schema({
  /**************************************************************************
   *                           Proxy Information                            *
   **************************************************************************/
  url: {
    type: String,
    required: true,
  },
  account: {
    type: String,
    required: true,
  },
  password: {
    type: String,
    required: true,
  },
  isInUse: {
    type: Boolean,
    default: false,
  },
});

export const Proxy = mongoose.model("Proxy", ProxySchema);
