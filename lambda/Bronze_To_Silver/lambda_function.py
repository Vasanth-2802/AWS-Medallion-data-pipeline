import boto3
import csv
import os
import tempfile
import urllib.parse

s3 = boto3.client("s3")
sns = boto3.client("sns")

# ==============================
# BUCKET CONFIGURATION
# ==============================

SILVER_BUCKET = "silver-layer-077489419604-us-east-1-an"
FAILED_BUCKET = "failed-layer-077489419604-us-east-1-an"

# ==============================
# SNS CONFIGURATION
# ==============================

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:077489419604:medallion-failure-alarts"


# ==============================
# LAMBDA HANDLER
# ==============================

def lambda_handler(event, context):

    print("========================================")
    print("Bronze_To_Silver started")
    print("========================================")

    bucket = None
    key = None

    try:

        # ==========================================
        # 1. GET S3 BUCKET AND FILE NAME
        # ==========================================

        bucket = event["Records"][0]["s3"]["bucket"]["name"]

        key = urllib.parse.unquote_plus(
            event["Records"][0]["s3"]["object"]["key"]
        )

        print(f"Source bucket: {bucket}")
        print(f"Source file: {key}")


        # ==========================================
        # 2. CHECK CSV FILE
        # ==========================================

        if not key.lower().endswith(".csv"):

            print("File is not CSV. Skipping.")

            return {
                "statusCode": 200,
                "message": "Non-CSV file skipped"
            }


        # ==========================================
        # 3. CREATE TEMPORARY FILES
        # ==========================================

        input_file = tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False
        )

        input_path = input_file.name
        input_file.close()


        output_file = tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            delete=False
        )

        output_path = output_file.name


        # ==========================================
        # 4. DOWNLOAD BRONZE FILE
        # ==========================================

        try:

            print("Downloading Bronze file...")

            s3.download_file(
                bucket,
                key,
                input_path
            )

            print("Download completed")


            # ==========================================
            # 5. READ CSV
            # ==========================================

            records_read = 0
            records_written = 0
            duplicates_removed = 0

            seen = set()


            with open(
                input_path,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as infile:

                reader = csv.DictReader(infile)


                # ==========================================
                # 6. VALIDATE HEADER
                # ==========================================

                if not reader.fieldnames:

                    raise Exception("CSV has no header")


                fieldnames = [
                    column.strip()
                    for column in reader.fieldnames
                ]

                print("Columns:")
                print(fieldnames)


                # ==========================================
                # 7. CREATE SILVER CSV
                # ==========================================

                writer = csv.DictWriter(
                    output_file,
                    fieldnames=fieldnames
                )

                writer.writeheader()


                # ==========================================
                # 8. CLEAN DATA + REMOVE DUPLICATES
                # ==========================================

                for row in reader:

                    records_read += 1

                    cleaned_row = {}

                    for column in fieldnames:

                        value = row.get(column, "")

                        if value is None:
                            value = ""

                        cleaned_row[column] = value.strip()


                    # Create unique key for duplicate detection
                    row_key = tuple(
                        cleaned_row[column]
                        for column in fieldnames
                    )


                    if row_key in seen:

                        duplicates_removed += 1

                        continue


                    seen.add(row_key)

                    writer.writerow(cleaned_row)

                    records_written += 1


            output_file.close()


            # ==========================================
            # 9. PRINT PROCESSING RESULTS
            # ==========================================

            print(f"Records read: {records_read}")

            print(
                f"Duplicates removed: "
                f"{duplicates_removed}"
            )

            print(
                f"Records written: "
                f"{records_written}"
            )


            # ==========================================
            # 10. CREATE SILVER FILE NAME
            # ==========================================

            filename = os.path.basename(key)

            silver_key = (
                "processed/cleaned_" + filename
            )


            # ==========================================
            # 11. UPLOAD TO SILVER
            # ==========================================

            print(
                f"Uploading to Silver: "
                f"{silver_key}"
            )

            s3.upload_file(
                output_path,
                SILVER_BUCKET,
                silver_key
            )

            print("Silver upload successful")


            # ==========================================
            # 12. SUCCESS RESPONSE
            # ==========================================

            return {
                "statusCode": 200,
                "message": "Bronze to Silver successful",
                "records_read": records_read,
                "records_written": records_written,
                "duplicates_removed": duplicates_removed,
                "silver_key": silver_key
            }


        finally:

            # ==========================================
            # 13. DELETE TEMPORARY FILES
            # ==========================================

            if os.path.exists(input_path):

                os.remove(input_path)


            if os.path.exists(output_path):

                os.remove(output_path)


    except Exception as e:

        # ==========================================
        # 14. BRONZE → SILVER FAILED
        # ==========================================

        print("========================================")
        print("Bronze_To_Silver FAILED")
        print(f"Error: {str(e)}")
        print("========================================")


        # ==========================================
        # 15. COPY FAILED FILE TO FAILED BUCKET
        # ==========================================

        if bucket and key:

            try:

                failed_key = (
                    "failed/"
                    + os.path.basename(key)
                )

                print(
                    f"Copying failed file to: "
                    f"s3://{FAILED_BUCKET}/{failed_key}"
                )


                s3.copy_object(

                    Bucket=FAILED_BUCKET,

                    CopySource={
                        "Bucket": bucket,
                        "Key": key
                    },

                    Key=failed_key
                )


                print("Failed file copied successfully")


            except Exception as copy_error:

                print(
                    "Failed to copy file to Failed bucket:"
                )

                print(str(copy_error))


        # ==========================================
        # 16. SEND SNS FAILURE NOTIFICATION
        # ==========================================

        try:

            message = (
                "Bronze to Silver processing failed.\n\n"
                f"Source Bucket: {bucket}\n"
                f"Source File: {key}\n"
                f"Error: {str(e)}\n\n"
                "The failed file has been copied "
                "to the Failed layer."
            )


            sns.publish(

                TopicArn=SNS_TOPIC_ARN,

                Subject=(
                    "Medallion Pipeline Failure - "
                    "Bronze to Silver"
                ),

                Message=message
            )


            print(
                "SNS failure notification "
                "sent successfully"
            )


        except Exception as sns_error:

            print(
                "Failed to send SNS notification:"
            )

            print(str(sns_error))


        # ==========================================
        # 17. RE-RAISE ERROR
        # ==========================================

        raise e
