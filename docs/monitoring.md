# CloudWatch Monitoring

Amazon CloudWatch is used to monitor the AWS Medallion Data Pipeline.

## Lambda Monitoring

The following Lambda functions are monitored:

- Bronze_To_Silver
- Silver_To_Gold

CloudWatch automatically collects Lambda execution metrics and logs.

## CloudWatch Logs

Lambda execution logs are available in CloudWatch Log Groups:

- /aws/lambda/Bronze_To_Silver
- /aws/lambda/Silver_To_Gold

The logs are used to monitor:

- Lambda execution
- Processing status
- Number of records processed
- Errors and exceptions
- Failed file processing
- S3 upload status

## CloudWatch Metrics

Important Lambda metrics include:

- Invocations
- Errors
- Duration
- Throttles
- Concurrent executions

## CloudWatch Alarms

CloudWatch alarms can be configured to monitor Lambda failures.

Example:

If the number of Lambda errors is greater than zero, CloudWatch can trigger an alarm.

## Pipeline Monitoring

The complete pipeline can be monitored using CloudWatch:

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

Failed processing:

Bronze_To_Silver Lambda
    |
    v
Failed S3
    |
    v
Amazon SNS
    |
    v
Email Notification

## Benefits

CloudWatch provides:

- Centralized Lambda logs
- Error monitoring
- Performance monitoring
- Failure detection
- Operational visibility
- Pipeline troubleshooting
