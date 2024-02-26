import { google } from "googleapis";
import fs from "fs/promises";
import readline from "readline/promises";
import dotenv from "dotenv";
dotenv.config();

const SCOPES = [
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/drive",
];
const TOKEN_PATH = "token.json";

async function authorize() {
  const content = {
    installed: {
      client_id: process.env.GOOGLE_CLIENT_ID,
      project_id: process.env.GOOGLE_PROJECT_ID,
      auth_uri: "https://accounts.google.com/o/oauth2/auth",
      token_uri: "https://oauth2.googleapis.com/token",
      auth_provider_x509_cert_url: "https://www.googleapis.com/oauth2/v1/certs",
      client_secret: process.env.GOOGLE_CLIENT_SECRET,
      redirect_uris: ["http://localhost", ""],
    },
  };
  const credentials = JSON.parse(content);
  const { client_secret, client_id, redirect_uris } = credentials.installed;
  const oAuth2Client = new google.auth.OAuth2(
    client_id,
    client_secret,
    redirect_uris[0]
  );

  try {
    const token = await fs.readFile(TOKEN_PATH);
    oAuth2Client.setCredentials(JSON.parse(token));
  } catch (error) {
    await getNewToken(oAuth2Client);
  }

  return oAuth2Client;
}

async function getNewToken(oAuth2Client) {
  const authUrl = oAuth2Client.generateAuthUrl({
    access_type: "offline",
    scope: SCOPES,
  });
  console.log("Authorize this app by visiting this url:", authUrl);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const code = await rl.question("Enter the code from that page here: ");
  const token = await oAuth2Client.getToken(code);
  await fs.writeFile(TOKEN_PATH, JSON.stringify(token.tokens));
  console.log("Token stored to", TOKEN_PATH);

  oAuth2Client.setCredentials(token.tokens);
}

async function createAndShareSheetHelper(auth, sheetName, email, question) {
  const sheets = google.sheets({ version: "v4", auth });

  // Create a new Google Sheet with the specified name
  const sheet = await sheets.spreadsheets.create({
    resource: {
      properties: {
        title: sheetName,
      },
    },
  });

  const sheetId = sheet.data.spreadsheetId;
  console.log(
    `Created Sheet "${sheetName}" with ID: ${sheetId}, and the url is https://docs.google.com/spreadsheets/d/${sheetId}`
  );

  // Share the Google Sheet with the specified email as an editor
  const drive = google.drive({ version: "v3", auth });
  await drive.permissions.create({
    fileId: sheetId,
    requestBody: {
      type: "user",
      role: "writer", // 'writer' permission allows the user to edit the sheet
      emailAddress: email, // The email address of the user to share with
    },
  });

  console.log(`Sheet "${sheetName}" shared with ${email} as an editor.`);

  // Add the question to the first row and first column of the sheet
  await sheets.spreadsheets.values.update({
    spreadsheetId: sheetId,
    range: "A1", // Specifies the first cell
    valueInputOption: "RAW", // The input value will be used as-is
    requestBody: {
      values: [[question]], // The question is placed in the first row, first column
    },
  });

  console.log(`Question "${question}" added to Sheet "${sheetName}".`);
  return sheetId;
}

export async function createAndShareSheet(
  sheetName,
  email,
  question,
  targetAmountResponse
) {
  const auth = await authorize();
  // const sheetName = "Your Sheet Name"; // Set your desired sheet name here
  // const email = "example@example.com"; // Set the email to share the sheet with here
  // const question = "Your Question Here"; // Set your question here

  const sheetId = await createAndShareSheetHelper(
    auth,
    sheetName,
    email,
    question
  );
  return sheetId;
}

export async function updateGoogleSheet(rowData, sheetId) {
  const auth = await authorize();
  const sheets = google.sheets({ version: "v4", auth });
  // Find the first empty row
  let range = "Sheet1"; // Default to the first sheet; adjust as needed
  let response = await sheets.spreadsheets.values.get({
    spreadsheetId: sheetId,
    range,
  });

  let firstEmptyRow = response.data.values
    ? response.data.values.length + 1
    : 1;

  // Prepare the range for the new row
  let updateRange = `Sheet1!A${firstEmptyRow}`; // Adjust 'Sheet1' if using a different sheet name

  // Prepare the request body
  let valueInputOption = "RAW"; // Values will be parsed as if entered into the UI
  let requestBody = {
    values: [rowData],
  };

  // Update the sheet with the new row of data
  await sheets.spreadsheets.values.update({
    spreadsheetId: sheetId,
    range: updateRange,
    valueInputOption,
    requestBody,
  });

  console.log(`Row added to Sheet ID ${sheetId} at row ${firstEmptyRow}`);
}
//test
//   const rowData = ['dyllan', 'linkedin.com', 'thanks'];
//   updateGoogleSheet(rowData, '1DROMgRDjRtZQzWUByqTTrLHY5lzJm72z_OPL_-V3FQE').catch(console.error);
