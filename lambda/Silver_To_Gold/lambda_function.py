import boto3
import csv
import io
import urllib.parse
import hashlib

# =========================================================
# S3 CLIENT
# =========================================================

s3 = boto3.client("s3")


# =========================================================
# GOLD BUCKET
# =========================================================

GOLD_BUCKET = "gold-layer-077489419604-us-east-1-an"


# =========================================================
# SETTINGS
# =========================================================

# Each S3 multipart-upload part must be at least 5 MB
# except the final part.
PART_SIZE = 8 * 1024 * 1024


# =========================================================
# LAMBDA HANDLER
# =========================================================

def lambda_handler(event, context):

    print("========================================")
    print("Silver_To_Gold started")
    print("========================================")

    upload_id = None

    try:

        # -------------------------------------------------
        # 1. Get Silver bucket and file information
        # -------------------------------------------------

        record = event["Records"][0]

        silver_bucket = record["s3"]["bucket"]["name"]

        silver_key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        print(f"Silver bucket: {silver_bucket}")
        print(f"Silver file: {silver_key}")


        # -------------------------------------------------
        # 2. Process only CSV files
        # -------------------------------------------------

        if not silver_key.lower().endswith(".csv"):

            print("File is not CSV. Skipping.")

            return {
                "statusCode": 200,
                "message": "Non-CSV file skipped"
            }


        # -------------------------------------------------
        # 3. Create Gold file name
        # -------------------------------------------------

        original_filename = silver_key.split("/")[-1]

        if original_filename.lower().endswith(".csv"):

            gold_filename = (
                original_filename[:-4] + "_gold.csv"
            )

        else:

            gold_filename = (
                original_filename + "_gold.csv"
            )


        # -------------------------------------------------
        # 4. Gold S3 path
        # -------------------------------------------------

        gold_key = f"gold/{gold_filename}"

        print(f"Gold bucket: {GOLD_BUCKET}")
        print(f"Gold file: {gold_key}")


        # -------------------------------------------------
        # 5. Download Silver file as streaming body
        # -------------------------------------------------

        print("Opening Silver file...")

        response = s3.get_object(
            Bucket=silver_bucket,
            Key=silver_key
        )

        body = response["Body"]

        print("Silver file opened successfully")


        # -------------------------------------------------
        # 6. Read CSV
        # -------------------------------------------------

        text_stream = io.TextIOWrapper(
            body,
            encoding="utf-8-sig",
            newline=""
        )

        reader = csv.DictReader(text_stream)

        if not reader.fieldnames:

            raise Exception(
                "CSV has no header"
            )


        # -------------------------------------------------
        # 7. Clean column names
        # -------------------------------------------------

        fieldnames = [
            column.strip()
            for column in reader.fieldnames
        ]

        print("Columns:")
        print(fieldnames)


        # -------------------------------------------------
        # 8. Start S3 multipart upload
        # -------------------------------------------------

        print("Starting Gold multipart upload...")

        multipart = s3.create_multipart_upload(
            Bucket=GOLD_BUCKET,
            Key=gold_key,
            ContentType="text/csv"
        )

        upload_id = multipart["UploadId"]

        print("Multipart upload started")


        # -------------------------------------------------
        # 9. Create first CSV buffer
        # -------------------------------------------------

        buffer = io.StringIO(
            newline=""
        )

        writer = csv.DictWriter(
            buffer,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()


        # -------------------------------------------------
        # 10. Counters
        # -------------------------------------------------

        input_rows = 0
        output_rows = 0

        duplicates_removed = 0
        empty_rows_removed = 0

        part_number = 1

        uploaded_parts = []


        # -------------------------------------------------
        # 11. Duplicate detection
        #
        # No SQLite.
        # Store only SHA256 hashes in memory.
        # -------------------------------------------------

        seen_hashes = set()


        # -------------------------------------------------
        # 12. Process rows
        # -------------------------------------------------

        for row in reader:

            input_rows += 1

            cleaned_row = {}


            # -------------------------------------------------
            # Clean every value
            # -------------------------------------------------

            for column in fieldnames:

                value = row.get(column, "")

                if value is None:

                    value = ""

                value = str(value).strip()

                cleaned_row[column] = value


            # -------------------------------------------------
            # Remove completely empty rows
            # -------------------------------------------------

            if all(
                value == ""
                for value in cleaned_row.values()
            ):

                empty_rows_removed += 1

                continue


            # -------------------------------------------------
            # Create hash for duplicate detection
            # -------------------------------------------------

            row_string = "||".join(
                cleaned_row[column]
                for column in fieldnames
            )

            row_hash = hashlib.sha256(
                row_string.encode("utf-8")
            ).hexdigest()


            # -------------------------------------------------
            # Check duplicate
            # -------------------------------------------------

            if row_hash in seen_hashes:

                duplicates_removed += 1

                continue


            # -------------------------------------------------
            # New row
            # -------------------------------------------------

            seen_hashes.add(row_hash)

            writer.writerow(cleaned_row)

            output_rows += 1


            # -------------------------------------------------
            # Upload buffer when it reaches PART_SIZE
            # -------------------------------------------------

            if buffer.tell() >= PART_SIZE:

                data = buffer.getvalue().encode(
                    "utf-8"
                )

                print(
                    f"Uploading part {part_number} "
                    f"({len(data)} bytes)"
                )

                part_response = s3.upload_part(
                    Bucket=GOLD_BUCKET,
                    Key=gold_key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=data
                )

                uploaded_parts.append({
                    "PartNumber": part_number,
                    "ETag": part_response["ETag"]
                })

                print(
                    f"Part {part_number} uploaded"
                )


                # -----------------------------------------
                # New buffer
                # -----------------------------------------

                buffer = io.StringIO(
                    newline=""
                )

                writer = csv.DictWriter(
                    buffer,
                    fieldnames=fieldnames,
                    lineterminator="\n"
                )

                part_number += 1


            # -------------------------------------------------
            # Progress log
            # -------------------------------------------------

            if input_rows % 10000 == 0:

                print(
                    f"Processed rows: {input_rows}, "
                    f"Output rows: {output_rows}, "
                    f"Duplicates removed: "
                    f"{duplicates_removed}"
                )


        # -------------------------------------------------
        # 13. Upload final part
        # -------------------------------------------------

        final_data = buffer.getvalue().encode(
            "utf-8"
        )


        # There should always be at least a header.
        if final_data:

            print(
                f"Uploading final part {part_number} "
                f"({len(final_data)} bytes)"
            )

            part_response = s3.upload_part(
                Bucket=GOLD_BUCKET,
                Key=gold_key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=final_data
            )

            uploaded_parts.append({
                "PartNumber": part_number,
                "ETag": part_response["ETag"]
            })


        # -------------------------------------------------
        # 14. Complete multipart upload
        # -------------------------------------------------

        print("Completing Gold upload...")

        s3.complete_multipart_upload(
            Bucket=GOLD_BUCKET,
            Key=gold_key,
            UploadId=upload_id,
            MultipartUpload={
                "Parts": uploaded_parts
            }
        )

        upload_id = None

        print("Gold file uploaded successfully")


        # -------------------------------------------------
        # 15. Close input stream
        # -------------------------------------------------

        text_stream.close()


        # -------------------------------------------------
        # 16. Final result
        # -------------------------------------------------

        print("----------------------------------------")
        print("Silver_To_Gold SUCCESS")
        print("----------------------------------------")
        print(f"Input rows: {input_rows}")
        print(f"Output rows: {output_rows}")
        print(
            f"Duplicates removed: "
            f"{duplicates_removed}"
        )
        print(
            f"Empty rows removed: "
            f"{empty_rows_removed}"
        )
        print(f"Gold bucket: {GOLD_BUCKET}")
        print(f"Gold file: {gold_key}")
        print(f"S3 parts uploaded: {len(uploaded_parts)}")
        print("----------------------------------------")


        return {
            "statusCode": 200,
            "message": (
                "Silver to Gold transformation successful"
            ),
            "gold_bucket": GOLD_BUCKET,
            "gold_key": gold_key,
            "input_rows": input_rows,
            "output_rows": output_rows,
            "duplicates_removed": duplicates_removed,
            "empty_rows_removed": empty_rows_removed
        }


    except Exception as e:

        print("----------------------------------------")
        print("Silver_To_Gold FAILED")
        print("----------------------------------------")
        print(str(e))
        print("----------------------------------------")


        # -------------------------------------------------
        # Abort multipart upload if something failed
        # -------------------------------------------------

        if upload_id:

            try:

                print(
                    "Aborting incomplete Gold upload..."
                )

                s3.abort_multipart_upload(
                    Bucket=GOLD_BUCKET,
                    Key=gold_key,
                    UploadId=upload_id
                )

                print(
                    "Incomplete upload aborted"
                )

            except Exception as abort_error:

                print(
                    f"Could not abort upload: "
                    f"{abort_error}"
                )


        raise e
