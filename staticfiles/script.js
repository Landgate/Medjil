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

  // Hide elements that should not be printed
  var elementsToHide = document.querySelectorAll('.no-print');
  for (var i = 0; i < elementsToHide.length; i++) {
    elementsToHide[i].style.display = 'none';
  }

  // Trigger the print dialog
  window.print();

  // Remove the print styles after printing
  document.head.removeChild(printStyles);
}

// Call the function when a button or link is clicked, for example
var printButton = document.getElementById('printButton');
printButton.addEventListener('click', changeToPrintFormat);

// Function to change an EDMI report to a certificate
function certificate(){
    // Script to switch between Report and certificate
    hide_heading = [
        "Calibration Distance Observations",
        "Uncertainty Budget - Uncertainty Sources",
        "Combined Uncertainty Budget - Total Distance Uncertainty",
        "Uncertainty Groups Contribution to Certified Distances",
        "Table of Observations, Corrections, Uncertainties and Residuals",
        "Residuals From Least Squares Fit of The Baseline Measurements",
        "Comparison of Raw Observations to Certified Slope Distances",
        "Return Phase Angle of Observed Distances"];
    
    // Get all <h> elements
    var h2Elements = document.querySelectorAll("h2");
    var h1Elements = document.querySelectorAll("h1");
    var header = document.querySelector("header");
    var footer = document.querySelector("footer");
    var nav = document.querySelector("nav");
    
    // Hide each element
    header.style.display = "none";
    footer.style.display = "none";
    nav.style.display = "none";

    
    h1Elements[0].innerHTML = "<B>EDMI Calibration Certificate</B>";

    // Check if the content of the <h2> element is in the array of headers
    h2Elements.forEach(function(h2Element) {
        if (hide_heading.includes(h2Element.textContent.trim())) {
            var parentElement = h2Element.parentNode;

            // Hide the parent element
            parentElement.style.display = "none";
        }
    })
    var inputFields = document.querySelectorAll("input");
    inputFields.forEach(function(inputField) {
        inputField.disabled = true;
    });
}