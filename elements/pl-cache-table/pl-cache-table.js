/* eslint-env browser */
window.PLCacheTable = function (uuid, options) {
  // make the id of the element use query selector to choose the table reset button we are looking for
  this.element = document
    .querySelector('[data-table-uuid="' + uuid + '"]')
    .closest(".c-tbl-block");
  // If not found, print error to console
  if (!this.element) {
    console.log("cache couldn't be retreived", uuid);
  }
  // store prefill values immediately when page loads
  this.originalPrefills = {};
  this.element.querySelectorAll("input.form-control").forEach((input) => {
    this.originalPrefills[input.getAttribute("name")] = input.dataset.prefill;
  });

  // Initialize reset button functionality
  this.resetButton = this.element.querySelector(".reset-button");
  if (!this.resetButton) {
    console.error("Reset button not found for UUID:", uuid);
    return;
  }
  //derived some of this code from script-editor (restoreoriginalbutton code)
  this.resetConfirmContainer = this.element.querySelector(
    ".reset-confirm-container"
  );
  this.resetConfirm = this.element.querySelector(".reset-confirm");
  this.resetCancel = this.element.querySelector(".reset-cancel");

  if (this.resetConfirmContainer && this.resetConfirm && this.resetCancel) {
    this.initResetButton();
  } else {
    console.error("Reset confirmation elements not found for UUID:", uuid);
  }

  // limit buttons to table width
  this.table = this.element.querySelector('table.cache-table');
  this.resetContainer = this.element.querySelector('.reset-button-container');
  
  if (this.table && this.resetContainer) {
    this.tableWidth = this.table.getBoundingClientRect().width; 
    this.resetContainer.style.width = `${this.tableWidth}px`;
  }
};
//copy pasted this entire part from script editor for confirmation
window.PLCacheTable.prototype.initResetButton = function () {
  this.resetButton.addEventListener("click", () => {
    this.resetButton.style.display = "none";
    this.resetConfirmContainer.style.display = "block";
    this.cancelWidth = this.resetConfirm.offsetWidth;
    this.resetCancel.style.width = `${this.cancelWidth}px`;
    this.resetConfirm.focus();
  });

  this.resetConfirm.addEventListener("click", () => {
    this.resetConfirmContainer.style.display = "none";
    this.resetButton.style.display = "block";
    this.resetButton.focus();
    this.resetToPrefillValues();
  });

  this.resetCancel.addEventListener("click", () => {
    this.resetConfirmContainer.style.display = "none";
    this.resetButton.style.display = "block";
    this.resetButton.focus();
  });
};

window.PLCacheTable.prototype.resetToPrefillValues = function () {
  // reset input values
  this.element.querySelectorAll("input.form-control").forEach((input) => {
    const originalValue = this.originalPrefills[input.getAttribute("name")];
    input.value = originalValue || "";
  });

  this.element
    .querySelectorAll(".badge-success, .badge-danger")
    .forEach((badge) => {
      badge.parentNode.removeChild(badge);
    });

  this.element.querySelectorAll(".input-group-text").forEach((text) => {
    text.parentNode.removeChild(text);
  });

  this.element
    .querySelectorAll('[data-toggle="popover"]')
    .forEach((popover) => {
      popover.removeAttribute("data-content");
      popover.removeAttribute("data-original-title");
    });
};

// Initialize all cache inputs on page load
document.addEventListener("DOMContentLoaded", function () {
  // Debug info - log all available UUIDs
  console.log(
    "Available reset buttons:",
    Array.from(document.querySelectorAll(".reset-button[data-table-uuid]")).map(
      (el) => el.getAttribute("data-table-uuid")
    )
  );

  // Try different selector strategies
  const resetButtons = document.querySelectorAll(
    ".reset-button[data-table-uuid]"
  );

  if (resetButtons.length === 0) {
    console.error("No reset buttons found on the page");
  }

  resetButtons.forEach((button) => {
    try {
      const uuid = button.getAttribute("data-table-uuid");
      console.log("Initializing PLCacheTable for UUID:", uuid);
      new window.PLCacheTable(uuid);
    } catch (e) {
      console.error("Error initializing cache input:", e);
    }
  });
});
