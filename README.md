# AWS Medallion Data Pipeline

## Project Overview

An AWS-based Medallion Architecture data pipeline that processes CSV files through Bronze, Silver, and Gold layers using Amazon S3 and AWS Lambda.

The pipeline also includes failure handling using a Failed S3 bucket, Amazon SNS notifications, AWS IAM security, and Amazon CloudWatch monitoring.

---

## Architecture

    CSV FILE
        |
        v
    Bronze S3
        |
        | S3 Object Created
        v
    Bronze_To_Silver Lambda
        |
        +----------------------+
        |                      |
     SUCCESS                FAILURE
        |                      |
        v                      v
    Silver S3              Failed S3
        |                      |
        | S3 Object Created    v
        v                    Amazon SNS
    Silver_To_Gold Lambda      |
        |                      v
        v                Email Notification
    Gold S3

---

## Data Flow

### 1. Bronze Layer

CSV files are uploaded to the Bronze S3 bucket under the `incoming/` prefix.

    Bronze S3
        |
        └── incoming/
              └── input.csv

An S3 Object Created event automatically triggers the `Bronze_To_Silver` Lambda function.

### 2. Bronze to Silver

The `Bronze_To_Silver` Lambda function:

- Reads CSV files from the Bronze S3 bucket.
- Validates the CSV file.
- Reads CSV records.
- Cleans column values.
- Removes duplicate records.
- Writes the cleaned data to the Silver S3 bucket.
- Logs processing information to CloudWatch.
- Handles processing failures.
- Sends SNS failure notifications.

Successful files are stored in:

    Silver S3
        |
        └── processed/
              └── cleaned_<filename>.csv

### 3. Silver to Gold

The `Silver_To_Gold` Lambda function is automatically triggered when a new CSV file is created under the Silver `processed/` prefix.

It:

- Reads processed CSV files from Silver S3.
- Performs the required transformation.
- Processes the records.
- Creates the final Gold dataset.
- Uploads the transformed data to the Gold S3 bucket.
- Logs processing information to CloudWatch.

Gold files are stored in:

    Gold S3
        |
        └── gold/
              └── <filename>_gold.csv

---

## Failed File Handling

If the `Bronze_To_Silver` Lambda encounters a processing error, the file is handled through the failure flow.

    Bronze S3
        |
        v
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

Failed files are stored in:

    Failed S3
        |
        └── failed/

Amazon SNS sends an email notification when a processing failure occurs.

---

## S3 Buckets

The project uses four S3 buckets.

| Layer | Purpose |
|---|---|
| Bronze | Stores incoming raw CSV files |
| Silver | Stores cleaned and processed CSV files |
| Gold | Stores final transformed data |
| Failed | Stores files that fail processing |

### Bronze

    bronze-layer-077489419604-us-east-1-an
    └── incoming/

### Silver

    silver-layer-077489419604-us-east-1-an
    └── processed/

### Gold

    gold-layer-077489419604-us-east-1-an
    └── gold/

### Failed

    failed-layer-077489419604-us-east-1-an
    └── failed/

---

## Lambda Functions

### Bronze_To_Silver

Purpose:

    Bronze S3 → Clean / Validate → Silver S3

Main responsibilities:

- Read Bronze CSV files.
- Validate input.
- Clean records.
- Remove duplicate records.
- Write processed files to Silver.
- Handle failures.
- Publish SNS failure notifications.
- Generate CloudWatch logs.

### Silver_To_Gold

Purpose:

    Silver S3 → Transform → Gold S3

Main responsibilities:

- Read Silver CSV files.
- Transform data.
- Process records.
- Generate Gold output.
- Upload output to Gold S3.
- Generate CloudWatch logs.

---

## S3 Event Triggers

### Bronze to Silver Trigger

Bucket:

    bronze-layer-077489419604-us-east-1-an

Event:

    All object create events

Prefix:

    incoming/

Suffix:

    .csv

Flow:

    New CSV uploaded
           |
           v
       Bronze S3
           |
           v
    Bronze_To_Silver Lambda

### Silver to Gold Trigger

Bucket:

    silver-layer-077489419604-us-east-1-an

Event:

    All object create events

Prefix:

    processed/

Suffix:

    .csv

Flow:

    New processed CSV
           |
           v
       Silver S3
           |
           v
    Silver_To_Gold Lambda

---

## AWS Services Used

### Amazon S3

Used for:

- Bronze data storage.
- Silver data storage.
- Gold data storage.
- Failed file storage.

### AWS Lambda

Used for:

- Bronze to Silver processing.
- Silver to Gold processing.
- Data validation.
- Data transformation.
- Failure handling.

### Amazon SNS

Used for:

- Failure notifications.
- Email alerts when pipeline processing fails.

### Amazon CloudWatch

Used for:

- Lambda execution logs.
- Error monitoring.
- Pipeline monitoring.
- CloudWatch alarms.
- Troubleshooting.

### AWS IAM

Used for:

- Lambda execution roles.
- S3 permissions.
- SNS publish permissions.
- Controlled access to AWS resources.

---

## IAM Security

The Lambda functions use the IAM role:

    medallion-lambda-role

The role provides controlled permissions required by the pipeline.

Permissions include:

- S3 GetObject.
- S3 PutObject.
- S3 ListBucket.
- SNS Publish.
- CloudWatch logging.

The principle of least privilege is followed by granting only the permissions required by the Lambda functions.

---

## Monitoring

Amazon CloudWatch is used to monitor the pipeline.

Monitoring includes:

- Lambda execution logs.
- Successful executions.
- Failed executions.
- Error messages.
- Execution duration.
- CloudWatch alarms.

Example monitoring flow:

    Lambda
       |
       v
    CloudWatch Logs
       |
       v
    Errors / Metrics
       |
       v
    CloudWatch Alarm

---

## Error Handling

The pipeline handles errors during processing.

    Input CSV
       |
       v
    Bronze_To_Silver
       |
       +---- Success ----> Silver
       |
       +---- Failure ----> Failed S3
                                |
                                v
                               SNS
                                |
                                v
                        Email Notification

This prevents failed files from being lost and provides notification when processing fails.

---

## Project Structure

    AWS-Medallion-data-pipeline/
    │
    ├── lambda/
    │   │
    │   ├── Bronze_To_Silver/
    │   │   └── lambda_function.py
    │   │
    │   └── Silver_To_Gold/
    │       └── lambda_function.py
    │
    ├── docs/
    │   │
    │   ├── architecture.md
    │   ├── aws-configuration.md
    │   ├── failed-file-handling.md
    │   └── monitoring.md
    │
    └── README.md

---

## Documentation

Detailed project documentation is available in the `docs` directory.

### Architecture

    docs/architecture.md

Contains the overall AWS Medallion Architecture and data flow.

### AWS Configuration

    docs/aws-configuration.md

Contains AWS services, configuration, IAM, S3, Lambda, SNS and CloudWatch details.

### Failed File Handling

    docs/failed-file-handling.md

Contains the failure flow and failed-file processing.

### Monitoring

    docs/monitoring.md

Contains CloudWatch monitoring, logs and alarms.

---

## Technologies Used

- Python
- AWS Lambda
- Amazon S3
- Amazon SNS
- Amazon CloudWatch
- AWS IAM
- CSV
- Boto3

---

## Key Features

- AWS Medallion Architecture.
- Bronze, Silver and Gold data layers.
- Automated S3 event triggers.
- Serverless data processing.
- CSV validation and cleaning.
- Duplicate record handling.
- Silver to Gold transformation.
- Failed file handling.
- SNS email notifications.
- CloudWatch monitoring.
- CloudWatch alarms.
- IAM-based security.
- Separation of raw, processed and final datasets.

---

## End-to-End Pipeline

    SOURCE CSV
        |
        v
    +-----------+
    | Bronze S3 |
    +-----------+
        |
        v
    Bronze_To_Silver Lambda
        |
        +---------+---------+
        |                   |
     SUCCESS              FAILURE
        |                   |
        v                   v
    Silver S3            Failed S3
        |                   |
        v                   v
    Silver_To_Gold         SNS
    Lambda                  |
        |                   v
        v              Email Alert
    Gold S3
        |
        v
    Final Dataset

---

## Project Outcome

The project demonstrates a complete serverless AWS data pipeline using the Medallion Architecture.

The pipeline automatically moves data through:

    Bronze → Silver → Gold

while providing:

    Failure Handling + SNS Notifications + CloudWatch Monitoring + IAM Security
