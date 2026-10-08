# AWS Medallion Architecture

## Architecture Flow

```text
CSV File
   |
   v
Bronze S3
   |
   v
Bronze_To_Silver Lambda
   |
   v
Silver S3
   |
   v
Silver_To_Gold Lambda
   |
   v
Gold S3

Failure Flow
Bronze_To_Silver Lambda
          |
          | Processing Failure
          v
      Failed S3
          |
          v
      Amazon SNS
          |
          v
    Email Notification
