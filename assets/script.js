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