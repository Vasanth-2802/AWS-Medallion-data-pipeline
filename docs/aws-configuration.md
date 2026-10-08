# AWS Configuration

## S3 Buckets

- Bronze Layer: bronze-layer
- Silver Layer: silver-layer
- Gold Layer: gold-layer
- Failed Layer: failed-layer

## AWS Lambda

### Bronze_To_Silver
Processes CSV files from the Bronze S3 layer and writes cleaned data to the Silver layer.

### Silver_To_Gold
Processes cleaned CSV files from the Silver layer and writes transformed data to the Gold layer.

## IAM

Lambda functions use the `medallion-lambda-role` IAM role to access the required S3 buckets and publish failure notifications to Amazon SNS.

## Amazon SNS

SNS is used to send email notifications when pipeline processing fails.

## Amazon CloudWatch

CloudWatch is used for:

- Lambda execution logs
- Error monitoring
- CloudWatch alarms
- Pipeline monitoring

## Data Flow

Bronze S3 → Bronze_To_Silver Lambda → Silver S3 → Silver_To_Gold Lambda → Gold S3

Failed processing → Failed S3 → SNS Email Notification
