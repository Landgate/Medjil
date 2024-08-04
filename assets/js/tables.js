/*

   © 2024 Western Australian Land Information Authority

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
  const rows = Array.from(table.rows).slice(1).filter(row => !row.querySelector("th")); // Exclude the header row
  const dir = header.dataset.sortDirection || "asc"; // Default sorting direction

  // Toggle sorting direction
  header.dataset.sortDirection = dir === "asc" ? "desc" : "asc";

  // Get the index of the clicked column
  const columnIndex = Array.from(header.parentNode.children).indexOf(header);

  // Sort the rows based on the column value
  rows.sort(function(a, b) {
    const aValue = parseCellValue(a.cells[columnIndex].textContent);
    const bValue = parseCellValue(b.cells[columnIndex].textContent);
    return dir === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
  });

  // Reorder the rows in the table
  rows.forEach(row => table.appendChild(row));
}

function parseCellValue(cellContent) {
  // Try to parse as a number
  const numericValue = parseFloat(cellContent);
  if (!isNaN(numericValue)) {
    return numericValue.toString();
  }

  // Try to parse as a date
  const dateValue = Date.parse(cellContent);
  if (!isNaN(dateValue)) {
    return new Date(dateValue).toISOString();
  }

  // Treat as text
  return cellContent.toLowerCase();
}