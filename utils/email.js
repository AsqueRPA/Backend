import dotenv from "dotenv";
import nodemailer from "nodemailer";
dotenv.config();

let mailTransporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: "hugozhan0802@gmail.com",
    pass: process.env.GOOGLE_APP_PASS,
  },
});

const sendEmail = async (subject, text) => {
  try {
    let mailDetails = {
      from: "hugozhan0802@gmail.com",
      to: "hugozhan0802@gmail.com",
      subject: subject,
      text: text,
    };
    return await mailTransporter.sendMail(mailDetails);
  } catch (err) {
    console.log(err);
  }
  return;
};

export { sendEmail };
