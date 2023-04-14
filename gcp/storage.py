from google.cloud import storage
import os

# TODO: more elegant way of setting this up
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../gcp_config.json"
client = storage.Client()


def upload_file_to_bucket(source_filename, dest_filename, bucket_name, rename=None):
    """
    Given local source file, upload file to bucket and rename to specfied
    dest_filename. Use '/' to specify directories.
    """

    bucket = client.get_bucket(bucket_name)

    # Upload a file to the bucket
    blob = bucket.blob(dest_filename)
    blob.upload_from_filename(source_filename)