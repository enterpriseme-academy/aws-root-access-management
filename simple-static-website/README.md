# Simple Static Website for AWS Root Access Management

This static website provides a user-friendly interface to interact with the AWS Root Access Management API.  
You can view and delete S3 bucket policies, and manage root account credentials using your API Gateway endpoints.

## Features

- **View S3 Bucket Policy**: Enter AWS Account Number and S3 Bucket Name, then click "Get S3 Bucket Policy" to view the current policy.
- **Delete S3 Bucket Policy**: Enter AWS Account Number and S3 Bucket Name, then click "Delete S3 Bucket Policy" to remove the policy.
- **Create Root Account**: Enter AWS Account Number and click "Create Root Account" to create a root login profile.
- **Delete Root Account**: Enter AWS Account Number and click "Delete Root Account" to delete the root login profile and deactivate MFA.

## Usage

1. Open `index.html` in your browser.
2. Fill in the required fields:
   - **AWS Account Number** (required for all actions)
   - **S3 Bucket Name** (required for bucket policy actions)
3. Click the appropriate button for your desired action.

## API Integration

- The website calls your API Gateway endpoints:
  - `GET /prod/unlock-s3-bucket/{account_number}/{bucket_name}` (Get S3 Bucket Policy)
  - `POST /prod/unlock-s3-bucket/{account_number}/{bucket_name}` (Delete S3 Bucket Policy)
  - `POST /prod/create-root-login-profile/{account_number}` (Create Root Account)
  - `POST /prod/delete-root-login-profile/{account_number}` (Delete Root Account)
- All requests require an API key, which is included in the `x-api-key` header in `src/scripts.js`.

## Output Formatting

- S3 bucket policy JSON is displayed with syntax highlighting and a dark theme, similar to VS Code.

## Customization

- Update the API endpoint URLs and API key in `src/scripts.js` if your deployment changes.
- You can further style the website by editing the `<style>` section in `index.html`.

## Security

- Your API key is hardcoded in `src/scripts.js` for demonstration.  
  For production, consider a more secure approach.

## Troubleshooting

- If you see CORS errors, ensure your API Gateway is configured with OPTIONS methods and CORS headers.
- If you see authentication errors, verify your API key and endpoint URLs.

## License

This project is licensed under the MIT License.