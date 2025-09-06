# AWS Account Management trusted access

Enabling trusted access between AWS Account Management and AWS Organizations lets your management account (or a delegated admin) centrally view and update member-account contact metadata through APIs, without signing in to each account.

---

## What it does

- **Scope:** Centralizes management of account-level contact data (for example, primary contact and alternate contacts for billing, operations, and security). It does not change root credentials or the root email address.
- **Who can act:** The management account, or a single delegated administrator you nominate for the organization.
- **How it’s wired:** You enable trusted access in Organizations, which authorizes the Account Management service to operate across your org using the member account IDs.
- **Prerequisite:** Your organization must be in All features mode.

---

## Key capabilities

- **Primary contact updates:** Change the account’s primary contact name, address, phone, and email for member accounts from a central place.
- **Alternate contacts:** Create, update, or remove Billing, Operations, and Security alternate contacts on member accounts.
- **Programmatic management:** Use consistent APIs to audit and remediate missing or out-of-date contacts at scale.
- **Delegated administration:** Assign a specific account (e.g., a platform/identity account) to manage contact data for all member accounts.
- **Auditable changes:** API calls are recorded in CloudTrail, enabling monitoring and compliance evidence.

---

## Benefits

- **Reduced need for root sign-in:** Central updates to contact data avoid using root credentials in each member account.
- **Consistent, up-to-date records:** Enforce standardized contacts across accounts to meet incident, billing, and compliance requirements.
- **Faster incident response:** Ensure security and operations teams are listed and reachable on every account for critical notifications.
- **Operational efficiency:** Automate onboarding/offboarding to set contacts correctly when accounts are created or transferred.
- **Clear separation of duties:** Delegate only the contact-management responsibility to a trusted admin account with least privilege.

---

## Potential issues and security concerns

- **Expanded blast radius:**  
  - **Risk:** If the management or delegated admin account is compromised, an attacker could change contact details across many accounts.  

---

## Enablement and governance recommendations

- **Enable trusted access:**  
  - **Step:** From the management account, enable trusted access for AWS Account Management in Organizations.  
  - **Note:** All features must be enabled in the org.

- **Choose a delegated admin (optional):**  
  - **Step:** Assign a dedicated platform/identity account as the delegated administrator to reduce risk concentration in the management account.

- **Harden the admin path:**  
  - **Controls:** MFA enforcement, strict IAM roles with session policies, short session durations, device and source IP conditions, and just-in-time access.

- **Define least-privilege policies:**  
  - **Scope:** Grant only the specific Account Management actions needed to read/write primary and alternate contacts; deny everywhere else by default.

- **Automate with guardrails:**  
  - **Practice:** Build idempotent jobs that set contacts based on a single source of truth; add pre-change validation and notifications.

- **Monitor and alert:**  
  - **Observability:** Create CloudTrail insights/EventBridge rules to alert on contact changes, especially deletes or bulk edits; log to a centralized, write-once destination.

- **Document boundaries:**  
  - **Clarity:** State explicitly that root email/password/MFA and other root-only tasks are out of scope and require separate, tightly controlled processes.

If you share your current org posture and tooling, I can tailor IAM/SCP snippets and a rollout plan with checks and alerts.