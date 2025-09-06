function syntaxHighlight(json) {
  if (typeof json != "string") {
    json = JSON.stringify(json, undefined, 2);
  }
  json = json
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    function (match) {
      let cls = "json-number";
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = "json-key";
        } else {
          cls = "json-string";
        }
      } else if (/true|false/.test(match)) {
        cls = "json-boolean";
      } else if (/null/.test(match)) {
        cls = "json-null";
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

function getBucketPolicy() {
  showSpinner();
  const accountNumber = document.getElementById("accountNumber").value;
  const bucketName = document.getElementById("bucketName").value;
  fetch(
    `https://ram.enterpriseme.academy/unlock-s3-bucket/${accountNumber}/${bucketName}`,
    {
      method: "GET",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      const output = document
        .getElementById("policyOutput")
        .querySelector("code");
      if (data.status === "success" && data.policy) {
        output.innerHTML = syntaxHighlight(data.policy);
      } else {
        output.textContent = data.message || "No policy found.";
      }
      hideSpinner();
    })
    .catch((error) => {
      console.error("Error fetching bucket policy:", error);
      const output = document
        .getElementById("policyOutput")
        .querySelector("code");
      output.textContent = "Error fetching bucket policy.";
      hideSpinner();
    });
}

function deleteBucketPolicy() {
  showSpinner();
  const accountNumber = document.getElementById("accountNumber").value;
  const bucketName = document.getElementById("bucketName").value;
  fetch(
    `https://ram.enterpriseme.academy/unlock-s3-bucket/${accountNumber}/${bucketName}`,
    {
      method: "POST",
    }
  )
    .then((response) => {
      if (response.ok) {
        alert("Bucket policy deleted successfully.");
        document.getElementById("policyOutput").textContent = "";
        hideSpinner();
      } else {
        alert("Failed to delete bucket policy.");
        hideSpinner();
      }
    })
    .catch((error) => {
      console.error("Error deleting bucket policy:", error);
      hideSpinner();
    });
}

function deleteRootAccount() {
  showSpinner();
  const accountNumber = document.getElementById("accountNumber").value;
  fetch(
    `https://ram.enterpriseme.academy/delete-root-login-profile/${accountNumber}`,
    {
      method: "POST",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      const output = document.getElementById("message").querySelector("code");
      if (data.status === "success") {
        output.textContent =
          data.message || "Root account deleted and MFA deactivated.";
      } else {
        output.textContent = data.message || "Failed to delete root account.";
      }
      hideSpinner();
    })
    .catch((error) => {
      console.error("Error deleting root account:", error);
      const output = document.getElementById("message").querySelector("code");
      output.textContent = "Error deleting root account.";
      hideSpinner();
    });
}

function createRootAccount() {
  showSpinner();
  const accountNumber = document.getElementById("accountNumber").value;
  fetch(
    `https://ram.enterpriseme.academy/create-root-login-profile/${accountNumber}`,
    {
      method: "POST",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      const output = document.getElementById("message").querySelector("code");
      if (data.status === "success") {
        output.textContent = data.message || "Root account created.";
      } else {
        output.textContent = data.message || "Failed to create root account.";
      }
      hideSpinner();
    })
    .catch((error) => {
      console.error("Error creating root account:", error);
      const output = document.getElementById("message").querySelector("code");
      output.textContent = "Error creating root account.";
      hideSpinner();
    });
}

function getSqsPolicy() {
  showSpinner();
  const accountNumber = document.getElementById("sqsAccountNumber").value;
  const queueName = document.getElementById("queueName").value;
  fetch(
    `https://ram.enterpriseme.academy/unlock-sqs-queue/${accountNumber}/${queueName}`,
    {
      method: "GET",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      const output = document
        .getElementById("sqsPolicyOutput")
        .querySelector("code");
      if (data.status === "success" && data.policy) {
        output.innerHTML = syntaxHighlight(data.policy);
      } else {
        output.textContent = data.message || "No policy found.";
      }
      hideSpinner();
    })
    .catch((error) => {
      console.error("Error fetching SQS queue policy:", error);
      const output = document
        .getElementById("sqsPolicyOutput")
        .querySelector("code");
      output.textContent = "Error fetching SQS queue policy.";
      hideSpinner();
    });
}

function deleteSqsPolicy() {
  showSpinner();
  const accountNumber = document.getElementById("sqsAccountNumber").value;
  const queueName = document.getElementById("queueName").value;
  fetch(
    `https://ram.enterpriseme.academy/unlock-sqs-queue/${accountNumber}/${queueName}`,
    {
      method: "POST",
    }
  )
    .then((response) => {
      if (response.ok) {
        alert("Queue policy deleted successfully.");
        document.getElementById("sqsPolicyOutput").textContent = "";
        hideSpinner();
      } else {
        alert("Failed to delete queue policy.");
        hideSpinner();
      }
    })
    .catch((error) => {
      console.error("Error deleting queue policy:", error);
      hideSpinner();
    });
}

document
  .getElementById("getPolicyButton")
  .addEventListener("click", getBucketPolicy);
document
  .getElementById("deletePolicyButton")
  .addEventListener("click", deleteBucketPolicy);
document
  .getElementById("deleteRootAccountButton")
  .addEventListener("click", deleteRootAccount);
document
  .getElementById("createRootAccountButton")
  .addEventListener("click", createRootAccount);
document
  .getElementById("getSqsPolicyButton")
  .addEventListener("click", getSqsPolicy);
document
  .getElementById("deleteSqsPolicyButton")
  .addEventListener("click", deleteSqsPolicy);
