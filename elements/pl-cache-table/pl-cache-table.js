/* eslint-env browser */
window.PLCacheTable = function (uuid, options) {
  // make the id of the element use query selector to choose the table reset button we are looking for
  this.element = document
    .querySelector('[data-table-uuid="' + uuid + '"]')
    ?.closest(".c-tbl-block");
  // If not found, print error to console and stop
  if (!this.element) {
    console.error("cache couldn't be retrieved", uuid);
    return;
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
  this.table = this.element.querySelector("table.cache-table");
  this.resetContainer = this.element.querySelector(".reset-button-container");

  if (this.table && this.resetContainer) {
    this.tableWidth = this.table.getBoundingClientRect().width;
    this.resetContainer.style.width = `${this.tableWidth}px`;
  }
};

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
    .querySelectorAll(".text-bg-success, .text-bg-danger")
    .forEach((badge) => {
      badge.parentNode.removeChild(badge);
    });

  this.element.querySelectorAll(".input-group-text").forEach((text) => {
    text.parentNode.removeChild(text);
  });

  this.element
    .querySelectorAll('[data-bs-toggle="popover"]')
    .forEach((popover) => {
      popover.removeAttribute("data-bs-content");
      popover.removeAttribute("data-bs-original-title");
    });
};

// Initialize all cache inputs on page load
document.addEventListener("DOMContentLoaded", function () {
  const resetButtons = document.querySelectorAll(
    ".reset-button[data-table-uuid]"
  );

  resetButtons.forEach((button) => {
    try {
      const uuid = button.getAttribute("data-table-uuid");
      new window.PLCacheTable(uuid);
    } catch (e) {
      console.error("Error initializing cache input:", e);
    }
  });
});
