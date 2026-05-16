/**
 * Sankalpa Google Sheets API — deploy as Web App (Execute as: Me, Access: Anyone).
 * Tabs: Users, Applications, Logs, Cache
 */
const SPREADSHEET_ID = "1p8NpBaJOTp6LIwwnemo_ZzgHDAR58FiPg53epNvDXYM";

function getSheet(sheetName) {
  const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  return spreadsheet.getSheetByName(sheetName);
}

function doGet(e) {
  const sheetName =
    e && e.parameter && e.parameter.sheet ? e.parameter.sheet : "Users";
  const sheet = getSheet(sheetName);
  if (!sheet) {
    return jsonResponse({ error: "Sheet not found: " + sheetName });
  }
  const data = sheet.getDataRange().getValues();
  return jsonResponse(data);
}

function doPost(e) {
  const body = JSON.parse(e.postData.contents);
  const sheet = getSheet(body.sheet);
  if (!sheet) {
    return jsonResponse({ error: "Sheet not found: " + body.sheet });
  }

  if (body.action === "update") {
    return jsonResponse(
      updateRow(sheet, body.key_column || 0, body.key_value, body.updates || {})
    );
  }

  if (body.row && body.row.length) {
    sheet.appendRow(body.row);
    return jsonResponse({ status: "success" });
  }

  return jsonResponse({ error: "Invalid post body" });
}

function updateRow(sheet, keyColumnIndex, keyValue, updates) {
  const data = sheet.getDataRange().getValues();
  if (data.length < 1) {
    return { status: "not_found" };
  }
  const headers = data[0];
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][keyColumnIndex]) === String(keyValue)) {
      for (const colName in updates) {
        if (!updates.hasOwnProperty(colName)) continue;
        const colIndex = headers.indexOf(colName);
        if (colIndex >= 0) {
          sheet.getRange(i + 1, colIndex + 1).setValue(updates[colName]);
        }
      }
      return { status: "updated", row: i + 1 };
    }
  }
  return { status: "not_found" };
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
