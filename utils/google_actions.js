import { google } from "googleapis";
import dotenv from "dotenv";
dotenv.config();

const SCOPES = [
  "https://www.googleapis.com/auth/spreadsheets",
  "https://www.googleapis.com/auth/drive",
];

function authorizeServiceAccount() {
  const serviceAccountAuth = new google.auth.GoogleAuth({
    credentials: JSON.parse(process.env.GOOGLE_CLOUD_CREDENTIALS),
    scopes: SCOPES,
  });
  return serviceAccountAuth;
}

export async function givePermission(sheetId, email) {
  const drive = google.drive({
    version: "v3",
    auth: authorizeServiceAccount(),
  });

  await drive.permissions.create({
    fileId: sheetId,
    requestBody: {
      type: "user",
      role: "writer",
      emailAddress: email,
    },
  });
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
  await givePermission(sheetId, email);
  await givePermission(sheetId, "hugozhan0802@gmail.com");
  await givePermission(sheetId, "dyllanliuuu@gmail.com");

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

export async function createAndShareSheet(sheetName, email, question) {
  const auth = authorizeServiceAccount();
  const sheetId = await createAndShareSheetHelper(
    auth,
    sheetName,
    email,
    question
  );
  return sheetId;
}

export async function addToGoogleSheet(rowData, sheetId) {
  const auth = authorizeServiceAccount();
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

export async function updateGoogleSheet(rowData, sheetId) {
  const auth = authorizeServiceAccount();
  const sheets = google.sheets({ version: 'v4', auth });
  
  // Read the first four columns where your data is located
  const range = 'Sheet1!A:D'; // Adjust 'Sheet1' and range as necessary
  const readResponse = await sheets.spreadsheets.values.get({
    spreadsheetId: sheetId,
    range: range,
  });
  const rows = readResponse.data.values || [];
  
  // Find the row number where all four column values match
  let rowNumber = rows.findIndex(row => 
    row.length >= 4 &&
    row[0] === rowData[0] &&
    row[1] === rowData[1] &&
    row[2] === rowData[2] &&
    row[3] === rowData[3]
  ) + 1; // +1 because Sheets is 1-indexed

  if (rowNumber === 0) {
    console.log('No matching row found');
    return; // No matching row found, exit the function
  }

  // Prepare the range for updating the found row
  let updateRange = `Sheet1!A${rowNumber}:I${rowNumber}`; // Adjust 'Sheet1' as necessary
  await sheets.spreadsheets.values.update({
    spreadsheetId: sheetId,
    range: updateRange,
    valueInputOption: 'RAW',
    requestBody: {
      values: [rowData], // newValues should be an array of new values for the row
    },
  });

  console.log(`Row ${rowNumber} updated in Sheet ID ${sheetId}`);
}

// const masterSheetRowData = [
//   "Matthew",
//   "matt@embeddables.com",
//   "Gowth Lead / VP Growth / Head of Growth / co-founder working on growth at consumer companies, seed - series C, ideally in software or healthcare",
//   "What is your biggest pain point right now when it comes to hitting your growth goals?",
//   30,
//   "true",
//   115,
//   1,
//   "https://docs.google.com/spreadsheets/d/" + "1KApWRrFzMhI2u9wADL2ohFbDIhAJv8EVPD3OnKhmkZo"
// ];

// updateGoogleSheet(masterSheetRowData, "1iuv7C1jg5fmeFfcRakH_e9U2_0nkEP98pkqtHpy3Uaw")

