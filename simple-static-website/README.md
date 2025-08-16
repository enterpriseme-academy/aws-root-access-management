# Simple Static Website

This project is a simple static website that allows users to interact with AWS S3 bucket policies. It provides an interface to retrieve and delete S3 bucket policies using API calls.

## Project Structure

```
simple-static-website
├── index.html          # Main HTML document for the static website
├── src
│   └── scripts.js      # JavaScript code for handling API calls
└── README.md           # Documentation for the project
```

## Features

- Input field for entering the S3 bucket name.
- Button to retrieve the S3 bucket policy via a GET API call.
- Button to delete the S3 bucket policy via a POST API call.
- Display of the S3 bucket policy in JSON format.

## Getting Started

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```
   cd simple-static-website
   ```

3. Open `index.html` in a web browser to view the static website.

## Usage

- Enter the S3 bucket name in the input field.
- Click "Get S3 bucket policy" to retrieve and display the policy.
- Click "Delete S3 bucket policy" to remove the policy from the specified S3 bucket.

## API Endpoints

- **GET** `/api/get-bucket-policy`: Retrieves the S3 bucket policy.
- **POST** `/api/delete-bucket-policy`: Deletes the S3 bucket policy.

## License

This project is licensed under the MIT License.