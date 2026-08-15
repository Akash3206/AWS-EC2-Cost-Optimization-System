# AWS EC2 Cost Optimization System

A serverless, event-driven AWS solution that automatically identifies non-production EC2 instances using tags and stops them on a scheduled basis, helping reduce unnecessary EC2 runtime costs.

## Tech Stack

* Python
* Boto3
* AWS Lambda
* Amazon EC2
* Amazon EventBridge
* AWS IAM
* Amazon CloudWatch

## Architecture

```text
EventBridge Scheduled Rule
          |
          v
     AWS Lambda
          |
          | Boto3
          v
   Amazon EC2
          |
          v
 Tag-based filtering
          |
          v
 Exclude protected instances
          |
          v
      Dry Run
          |
          v
   Stop Instances
          |
          v
   CloudWatch Logs
```

## How It Works

1. EventBridge triggers the Lambda according to a configured schedule.
2. Lambda finds running EC2 instances with the configured target tag.
3. Instances with the exclusion tag are skipped.
4. Dry-run mode validates the stop operation without actually stopping instances.
5. When dry-run mode is disabled, the selected EC2 instances are stopped.
6. Lambda execution details are recorded in CloudWatch Logs.

## EC2 Tagging Strategy

Instances managed by the system use:

```text
midnight=0
```

Instances that must remain running use:

```text
do-not-stop=true
```

| Tag           | Value  | Purpose                        |
| ------------- | ------ | ------------------------------ |
| `midnight`    | `0`    | Select instance for shutdown   |
| `do-not-stop` | `true` | Exclude instance from shutdown |

## Lambda Environment Variables

| Variable            | Default       | Purpose                                         |
| ------------------- | ------------- | ----------------------------------------------- |
| `DRY_RUN`           | `true`        | Controls whether instances are actually stopped |
| `TARGET_TAG_KEY`    | `midnight`    | Target tag key                                  |
| `TARGET_TAG_VALUE`  | `0`           | Target tag value                                |
| `EXCLUDE_TAG_KEY`   | `do-not-stop` | Exclusion tag key                               |
| `EXCLUDE_TAG_VALUE` | `true`        | Exclusion tag value                             |
| `LOG_LEVEL`         | `INFO`        | Logging level                                   |

## AWS Setup

### 1. Create the Lambda Function

Create an AWS Lambda function using a Python runtime.

Upload `lambda_function.py`.

Set the handler to:

```text
lambda_function.lambda_handler
```

### 2. Configure IAM

Create or assign an IAM execution role to the Lambda with permissions to:

```text
ec2:DescribeInstances
ec2:StopInstances
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
```

### 3. Configure Environment Variables

Add the following Lambda environment variables:

```text
DRY_RUN=true
TARGET_TAG_KEY=midnight
TARGET_TAG_VALUE=0
EXCLUDE_TAG_KEY=do-not-stop
EXCLUDE_TAG_VALUE=true
LOG_LEVEL=INFO
```

### 4. Tag the EC2 Instances

For an EC2 instance that should be managed:

```text
Key: midnight
Value: 0
```

For an instance that should be protected:

```text
Key: do-not-stop
Value: true
```

### 5. Create an EventBridge Schedule

1. Open **Amazon EventBridge**.
2. Create a new **Rule**.
3. Select **Schedule** as the rule type.
4. Configure the desired recurring schedule.
5. Select the Lambda function as the target.
6. Create and enable the rule.

### 6. Test the Lambda

Keep:

```text
DRY_RUN=true
```

Run the Lambda manually from the **Test** tab and verify the CloudWatch logs.

### 7. Enable Actual Shutdown

After confirming that the correct instances are selected:

```text
DRY_RUN=false
```

Deploy the configuration and allow EventBridge to trigger the Lambda according to the configured schedule.

## Cost Optimization

If an EC2 instance normally runs for 24 hours but only needs to run for 8 hours:

```text
Runtime reduction = (24 - 8) / 24
                  = 66.7%
```

Actual savings depend on the instance type, AWS region, runtime, and other associated resources.

## Project Structure

```text
AWS-EC2-Cost-Optimization-System/
├── lambda_function.py
├── README.md
└── .gitignore
```

## Security

* Use IAM roles instead of hard-coded AWS credentials.
* Follow least-privilege IAM practices.
* Keep dry-run mode enabled while testing.
* Use exclusion tags to protect critical instances.
* Review CloudWatch logs before enabling actual shutdowns.

## Future Improvements

* Automatically start instances during business hours.
* Support different schedules for different environments.
* Add SNS notifications.
* Add CloudWatch alarms.
* Track estimated cost savings.
* Add a cost-savings dashboard.
