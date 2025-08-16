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
  const accountNumber = document.getElementById("accountNumber").value;
  const bucketName = document.getElementById("bucketName").value;
  fetch(
    `https://upvs5kpmgb.execute-api.eu-central-1.amazonaws.com/prod/unlock-s3-bucket/${accountNumber}/${bucketName}`,
    {
      method: "GET",
      headers: {
        "x-api-key": "FugkibvSVV1mEUtFHm4WX1FvR6MOgigU8gEORyG1",
      },
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
    })
    .catch((error) => {
      console.error("Error fetching bucket policy:", error);
      const output = document
        .getElementById("policyOutput")
        .querySelector("code");
      output.textContent = "Error fetching bucket policy.";
    });
}

function deleteBucketPolicy() {
  const accountNumber = document.getElementById("accountNumber").value;
  const bucketName = document.getElementById("bucketName").value;
  fetch(
    `https://upvs5kpmgb.execute-api.eu-central-1.amazonaws.com/prod/unlock-s3-bucket/${accountNumber}/${bucketName}`,
    {
      method: "POST",
      headers: {
        "x-api-key": "FugkibvSVV1mEUtFHm4WX1FvR6MOgigU8gEORyG1",
      },
    }
  )
    .then((response) => {
      if (response.ok) {
        alert("Bucket policy deleted successfully.");
        document.getElementById("policyOutput").textContent = "";
      } else {
        alert("Failed to delete bucket policy.");
      }
    })
    .catch((error) => {
      console.error("Error deleting bucket policy:", error);
    });
}

function deleteRootAccount() {
  const accountNumber = document.getElementById("accountNumber").value;
  fetch(
    `https://upvs5kpmgb.execute-api.eu-central-1.amazonaws.com/prod/delete-root-login-profile/${accountNumber}`,
    {
      method: "POST",
      headers: {
        "x-api-key": "FugkibvSVV1mEUtFHm4WX1FvR6MOgigU8gEORyG1",
      },
    }
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        alert("Root account deleted and MFA deactivated.");
      } else {
        alert(data.message || "Failed to delete root account.");
      }
    })
    .catch((error) => {
      console.error("Error deleting root account:", error);
    });
}

function createRootAccount() {
  const accountNumber = document.getElementById("accountNumber").value;
  fetch(
    `https://upvs5kpmgb.execute-api.eu-central-1.amazonaws.com/prod/create-root-login-profile/${accountNumber}`,
    {
      method: "POST",
      headers: {
        "x-api-key": "FugkibvSVV1mEUtFHm4WX1FvR6MOgigU8gEORyG1",
      },
    }
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        alert("Root account created.");
      } else {
        alert(data.message || "Failed to create root account.");
      }
    })
    .catch((error) => {
      console.error("Error creating root account:", error);
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
