/*

   © 2023 Western Australian Land Information Authority

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
const toggle = document.querySelector(".toggle");
const menu = document.querySelector('.nav-links');

function toggleMenu() {
        if (menu.classList.contains("active")) {
            menu.classList.remove("active");
            toggle.querySelector("a").innerHTML = "<i class='fas fa-bars'></i>"
        } else {
            menu.classList.add("active");
            toggle.querySelector("a").innerHTML = "<i class='fas fa-times'></i>"
        }
    }

toggle.addEventListener('click', toggleMenu, false)

const items = document.querySelectorAll(".nav-item");

/* Activate Submenu */
function toggleItem() {
    if (this.classList.contains("sub-links-active")) {
      this.classList.remove("sub-links-active");
    } else if (menu.querySelector(".sub-links-active")) {
      menu.querySelector(".sub-links-active").classList.remove("sub-links-active");
      this.classList.add("sub-links-active");
    } else {
      this.classList.add("sub-links-active");
    }
  }
  
  /* Close Submenu From Anywhere */
  function closeSubmenu(e) {
    let isClickInside = menu.contains(e.target);
  
    if (!isClickInside && menu.querySelector(".sub-links-active")) {
      menu.querySelector(".sub-links-active").classList.remove("sub-links-active");
    }
  }
  /* Event Listeners */
  toggle.addEventListener("click", toggleMenu, false);
  for (let item of items) {
    if (item.querySelector(".sub-links")) {
      item.addEventListener("click", toggleItem, false);
    }
    item.addEventListener("keypress", toggleItem, false);
  }
  document.addEventListener("click", closeSubmenu, false);
  
// Find your wrapper HTMLElement
var wrapper = document.querySelector('.wrapper');

// Replace the whole wrapper with its own contents
// wrapper.outerHTML = wrapper.innerHTML;

function changeToPrintFormat() {
  event.preventDefault();
  // Create a new stylesheet for print styles
  var printStyles = document.createElement('style');
  printStyles.setAttribute('media', 'print');
  document.head.appendChild(printStyles);

  // Add CSS rules for print styles
  printStyles.sheet.insertRule('body { font-size: 12pt; }', 0);
  printStyles.sheet.insertRule('.no-print { display: none; }', 0);

  // Trigger the print dialog
  window.print();

  // Remove the print styles after printing
  document.head.removeChild(printStyles);
}

// Call the function when a button or link is clicked, for example
var printButton = document.getElementById('printButton');
printButton.addEventListener('click', changeToPrintFormat);

// Function to show the terms and conditions banner
function showTermsBanner() {
    const termsBanner = document.getElementById('termsBanner');
    termsBanner.style.display = 'block';
}

// Function to hide the terms and conditions banner and overlay
function hideTermsBanner() {
    const termsBanner = document.getElementById('termsBanner');
    termsBanner.style.display = 'none';

    document.cookie = 'medjilTerms=true; expires=Fri, 31 Dec 9999 23:59:59 GMT; path=/';
}

// Function to check if the user has already accepted the terms
function checkAcceptedTerms() {
    const cookies = document.cookie.split(';');
    return cookies.some(cookie => cookie.trim() === 'medjilTerms=true');
}

// Entry point: Check if the user has already accepted the terms, and if not, show the banner and disable user interaction
window.addEventListener('load', () => {
    if (!checkAcceptedTerms()) {
        showTermsBanner();
    }
});

// Event listener for the "Accept" button in the banner
document.getElementById('acceptTCButton').addEventListener('click', hideTermsBanner);

