import functions_framework
import json
import csv
from io import StringIO
from google.cloud import storage, bigquery

@functions_framework.cloud_event
def hello_gcs(cloud_event):
    data = cloud_event.data
    bucket = data["bucket"]
    name = data["name"]
    timeCreated = data["timeCreated"]

    if not name.endswith('.json'):
        print("Skipping non-JSON file")
        return

    try:
        storage_client = storage.Client()
        bq_client = bigquery.Client()

        # 1. Download and parse JSON
        bucket_obj = storage_client.bucket(bucket)
        blob = bucket_obj.blob(name)
        json_data = json.loads(blob.download_as_text())
        issues = json_data.get("issues", [])

        # 2. Add metadata to each issue
        for issue in issues:
            issue["file_upload_time"] = timeCreated
            issue["source_file"] = name

        # 3. Upload to BigQuery
        dataset_id = "security_scans"
        table_id = "issues_data"
        
        job = bq_client.load_table_from_json(
            issues,
            f"{dataset_id}.{table_id}",
            job_config=bigquery.LoadJobConfig(
                autodetect=True,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition="WRITE_APPEND"
            )
        )
        job.result()
        print(f"Loaded {job.output_rows} rows to BigQuery")

        # 4. Generate and upload CSV (memory-efficient streaming)
        output_bucket = "your-processed-csvs" # Replace with your CSV bucket name
        output_filename = f"processed/{name.replace('.json', '.csv')}"
        
        with StringIO() as csv_buffer:
            if issues: # Check if issues list is not empty
                writer = csv.DictWriter(csv_buffer, fieldnames=issues[0].keys())
                writer.writeheader()
                writer.writerows(issues)
            
                output_blob = storage_client.bucket(output_bucket).blob(output_filename)
                output_blob.upload_from_string(
                    csv_buffer.getvalue(),
                    content_type="text/csv"
                )
                print(f"CSV saved to gs://{output_bucket}/{output_filename}")

    except Exception as e:
        print(f"Error processing {name}: {str(e)}")
        raise