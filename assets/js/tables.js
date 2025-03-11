/*

   © 2025 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

*/


function sortTable(header) {
  const table = header.closest("table");
  const allRows = Array.from(table.rows);

  // Find the last header row
  let lastHeaderIndex = 0;
  allRows.forEach((row, index) => {
    if (row.querySelector("th")) {
      lastHeaderIndex = index;
    }
  });

  // Filter out header rows
  const rows = allRows.slice(lastHeaderIndex + 1);

  const dir = header.dataset.sortDirection || "asc"; // Default sorting direction

  // Toggle sorting direction
  header.dataset.sortDirection = dir === "asc" ? "desc" : "asc";

  // Calculate the correct column index
  const columnIndex = getColumnIndex(header);

  // Sort the rows based on the column value
  rows.sort(function(a, b) {
    const aValue = parseCellValue(a.cells[columnIndex].textContent);
    const bValue = parseCellValue(b.cells[columnIndex].textContent);
    return compareValues(aValue, bValue, dir);
  });

  // Reorder the rows in the table
  rows.forEach(row => table.appendChild(row));
}

function getColumnIndex(header) {
  const headersInRow = Array.from(header.parentNode.children);
  let columnIndex = 0;

  for (let i = 0; i < headersInRow.length; i++) {
    const th = headersInRow[i];
    if (th === header) {
      break;
    }
    columnIndex += th.colSpan || 1;
  }
  
  return columnIndex;
}

function parseCellValue(cellContent) {
  // Try to parse as a number
  const numericValue = parseFloat(cellContent);
  if (!isNaN(numericValue)) {
    return numericValue;
  }

  // Try to parse as a date
  const dateValue = Date.parse(cellContent);
  if (!isNaN(dateValue)) {
    return new Date(dateValue);
  }

  // Treat as text
  return cellContent.toLowerCase();
}

function compareValues(aValue, bValue, dir) {
  if (typeof aValue === "number" && typeof bValue === "number") {
    return dir === "asc" ? aValue - bValue : bValue - aValue;
  } else if (aValue instanceof Date && bValue instanceof Date) {
    return dir === "asc" ? aValue - bValue : bValue - aValue;
  } else {
    return dir === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
  }
}