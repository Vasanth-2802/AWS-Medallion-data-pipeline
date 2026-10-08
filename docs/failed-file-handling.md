# Failed File Handling

The pipeline includes failure handling in the Bronze-to-Silver Lambda.

## Failure Flow

Bronze S3
    ↓
Bronze_To_Silver Lambda
    ↓
Validation / Processing
    ↓
If processing fails
    ↓
Failed S3 Bucket
    ↓
Amazon SNS
    ↓
Email Notification

## Failed S3 Location

Failed files are stored in:

`failed/`

Example:

`failed/empty_failure_test.csv`

## Failure Scenarios

The Lambda handles failures such as:

- Empty CSV files
- CSV files without headers
- Invalid CSV data
- Processing exceptions
- S3 processing errors

## CloudWatch Logging

All failures are written to the Lambda CloudWatch log group:

`/aws/lambda/Bronze_To_Silver`

Example log messages:

`Bronze_To_Silver FAILED`

`CSV has no header`

`Failed file copied successfully`

## SNS Notification

When a processing failure occurs, the Lambda publishes a notification to the SNS topic:

`medallion-failure-alerts`

The SNS topic has an email subscription for failure notifications.
