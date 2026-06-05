from google.cloud import storage

print("Starting...")

try:
    client = storage.Client.from_service_account_json(
        "credentials/csigradservice.json"
    )

    print("Connected")

    bucket = client.bucket("csigrad-data-lake")

    print("Bucket found")

    blob = bucket.blob("raw/raw_data.csv")

    blob.upload_from_filename("raw_data/raw_data.csv")

    print("Upload successful")

except Exception as e:
    print("ERROR:")
    print(e)