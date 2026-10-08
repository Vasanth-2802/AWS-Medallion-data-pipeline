# AWS Medallion Data Pipeline

## Project Overview

An AWS-based Medallion Architecture data pipeline that processes CSV files through Bronze, Silver, and Gold layers using Amazon S3 and AWS Lambda.

## Architecture

Bronze S3
↓
Bronze_To_Silver Lambda
↓
Silver S3
↓
Silver_To_Gold Lambda
↓
Gold S3

Invalid File
↓
Failed S3
↓
Amazon SNS
↓
Email Notification

## AWS Services Used

- Amazon S3
- AWS Lambda
- AWS IAM
- Amazon SNS
- Amazon CloudWatch

## Data Layers

### Bronze Layer

Stores raw CSV files received from the source.

**S3 folder:** `incoming/`

### Silver Layer

Cleans and validates the raw CSV data.

**S3 folder:** `processed/`

Processing includes:

- CSV validation
- Header validation
- Data cleaning
- Duplicate handling
- Empty data handling

### Gold Layer

Stores transformed and business-ready data.

**S3 folder:** `gold/`

## Failure Handling

If an invalid or corrupted CSV file causes processing to fail:

1. Lambda detects the failure.
2. The failed file is copied to the Failed S3 bucket.
3. The failure is recorded in CloudWatch Logs.
4. Amazon SNS sends an email notification.

## Lambda Functions

### Bronze_To_Silver

Reads files from the Bronze S3 layer, validates and cleans the data, and writes the result to the Silver layer.

### Silver_To_Gold

Reads processed files from the Silver layer, transforms the data, and writes the final data to the Gold layer.

## Monitoring

Amazon CloudWatch is used for:

- Lambda execution logs
- Error monitoring
- CloudWatch alarms
- Pipeline monitoring

## Security

AWS IAM provides controlled permissions for Lambda to access the required S3 buckets and SNS topic.

## Technologies

Python | AWS Lambda | Amazon S3 | IAM | SNS | CloudWatch | CSV | Medallion Architecture | Data Engineering
