# Centralized Root Access for AWS Organizations

Enable centralized root access to remove, recover, and perform specific root-level tasks on member accounts without using each account’s root credentials.

---

## Actions Available from the Management Account

- Delete root credentials on a member account—including the root user password, access keys, signing certificates, and deactivating MFA.  
- Enable password recovery for the root user of a member account to re-enable its root profile.  
- Delete misconfigured Amazon S3 bucket policies that deny all principals access to a bucket.  
- Delete misconfigured Amazon SQS resource-based policies that deny all principals access to a queue.  

You can launch privileged root sessions in the AWS Management Console under **Root access management**, or programmatically via the AWS CLI/API using `sts:AssumeRoot` with scoped task policies such as `IAMDeleteRootUserCredentials`, `S3UnlockBucketPolicy`, and `SQSUnlockQueuePolicy`.

---

## Tasks That Require Re-enabling the Root Profile on a Member Account

Certain operations are not supported by centralized privileged sessions and require direct root-user sign-in on the member account:

### Account Management
- Change the root user password, email address, and access keys.  
- Create or remove root user signing certificates and configure MFA (beyond deactivation).  
- Close an AWS account when Organizations features are not in use or disabled.

### Security and Recovery
- Restore IAM user permissions if the only IAM administrator accidentally revoked their own access.

### Billing
- Activate IAM access to the Billing and Cost Management console and perform billing operations limited to the root user.  
- View and download tax invoices for AWS Inc. or Amazon Internet Services Private Limited (AISPL) (IAM users can only download VAT invoices from AWS Europe).

### Specialized AWS Services
- Sign up for AWS GovCloud (US) and request GovCloud root user access keys from AWS Support.  
- Register as a seller in the Reserved Instance Marketplace (Amazon EC2).  
- Recover unmanageable AWS KMS keys via Support using the root user’s primary phone number for authorization.  
- Link an AWS account to an Amazon Mechanical Turk Requester account.  
- Configure Amazon S3 buckets to require MFA for privileged operations and perform other S3 or SQS policy edits not covered by privileged sessions.

---

## Re-enabling the Root Profile and Obtaining a Root Password

1. Sign in to your AWS Organizations management account (or delegated administrator) and open the IAM console at https://console.aws.amazon.com/iam/.  
2. In the navigation pane, choose **Root access management**.  
3. Select the target member account and click **Take privileged action** → **Allow password recovery** to enable root-user password resets for that account.  
4. Instruct the holder of the member account’s root user email address to go to the AWS sign-in page, click **Forgot password**, enter their email, and follow the reset link to set a new password.  
5. After resetting, sign in to the AWS Management Console as the root user of the member account.  
6. Recreate or rotate root access keys and signing certificates as needed, and configure multi-factor authentication on the root account.  
7. Once root-level tasks are complete, use the **Delete root credentials** privileged action again to remove long-term root credentials and maintain centralized access security.

---

**References**  
1. AWS account root user – AWS Identity and Access Management User Guide: Tasks that require root user credentials and best practices  
2. Perform a privileged task on an AWS Organizations member account – AWS Identity and Access Management User Guide: Short-term root sessions and privileged actions