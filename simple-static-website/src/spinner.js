// Spinner control functions
function showSpinner() {
  const spinner = document.getElementById("progressSpinner");
  if (spinner) spinner.classList.remove("hidden");
}

function hideSpinner() {
  const spinner = document.getElementById("progressSpinner");
  if (spinner) spinner.classList.add("hidden");
}
