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
  var table = header.closest("table");
  var rows = Array.from(table.rows).slice(1).filter(row => !row.querySelector("th")); // Exclude the header row
  var dir = header.dataset.sortDirection || "asc"; // Default sorting direction

  // Toggle sorting direction
  dir = dir === "asc" ? "desc" : "asc";
  header.dataset.sortDirection = dir;

  // Get the index of the clicked column
  var columnIndex = Array.from(header.parentNode.children).indexOf(header);

  // Sort the rows based on the column value
  rows.sort(function(a, b) {
    var aValue = a.cells[columnIndex].textContent.toLowerCase();
    var bValue = b.cells[columnIndex].textContent.toLowerCase();
    return dir === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
  });

  // Reorder the rows in the table
  rows.forEach(function(row) {
    table.appendChild(row);
  });
}