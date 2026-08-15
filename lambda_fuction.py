import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

ec2 = boto3.client("ec2")

DRY_RUN = os.environ.get("DRY_RUN", "true").lower() in ("1", "true", "yes")
EXCLUDE_TAG_KEY = os.environ.get("EXCLUDE_TAG_KEY", "do-not-stop")
EXCLUDE_TAG_VALUE = os.environ.get("EXCLUDE_TAG_VALUE", "true")
TARGET_TAG_KEY = os.environ.get("TARGET_TAG_KEY", "midnight")
TARGET_TAG_VALUE = os.environ.get("TARGET_TAG_VALUE", "0")


def lambda_handler(event, context):
    logger.info("Lambda started. DRY_RUN=%s", DRY_RUN)

    try:
        filters = [
            {"Name": f"tag:{TARGET_TAG_KEY}", "Values": [TARGET_TAG_VALUE]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]

        response = ec2.describe_instances(Filters=filters)
        instance_to_stop = []

        for reservation in response.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                instance_id = inst.get("InstanceId")

                tags = (
                    {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                    if inst.get("Tags")
                    else {}
                )

                if tags.get(EXCLUDE_TAG_KEY) == EXCLUDE_TAG_VALUE:
                    logger.info(
                        "Skipping instance %s due to exclude tag %s=%s",
                        instance_id,
                        EXCLUDE_TAG_KEY,
                        EXCLUDE_TAG_VALUE,
                    )
                    continue

                instance_to_stop.append(instance_id)

        if not instance_to_stop:
            logger.info(
                "No running instances found with tag %s=%s",
                TARGET_TAG_KEY,
                TARGET_TAG_VALUE,
            )
            return {"stopped": [], "dry_run": DRY_RUN}

        logger.info("Instances selected to stop: %s", instance_to_stop)

        # DRY RUN
        if DRY_RUN:
            try:
                ec2.stop_instances(
                    InstanceIds=instance_to_stop,
                    DryRun=True,
                )
            except ClientError as e:
                if e.response.get("Error", {}).get("Code") == "DryRunOperation":
                    logger.info("Dry run successful (permissions OK).")
                else:
                    logger.error("Dry run failed: %s", e)
                    raise

            return {
                "stopped": instance_to_stop,
                "dry_run": True,
            }

        # REAL STOP
        try:
            stop_resp = ec2.stop_instances(
                InstanceIds=instance_to_stop
            )

            logger.info("StopInstances response: %s", stop_resp)

            stopped_ids = [
                i["InstanceId"]
                for i in stop_resp.get("StoppingInstances", [])
            ]

            return {
                "stopped": stopped_ids,
                "dry_run": False,
            }

        except ClientError as e:
            logger.error("Failed to stop instances: %s", e)
            raise

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise