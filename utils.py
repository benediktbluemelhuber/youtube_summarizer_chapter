from google.cloud import storage
from google.oauth2 import service_account
import streamlit as st
import yaml


# Global configuration variable
current_config = None

def download_blob_from_gcs(bucket_name, blob_name, destination_file_name):
    """Downloads a blob from GCS and stores it to the destination file."""
    # Get GCS credentials from Streamlit secrets
    gcs_credentials = service_account.Credentials.from_service_account_info(st.secrets["gcs"])

    # Create a client using these credentials
    storage_client = storage.Client(credentials=gcs_credentials)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.download_to_filename(destination_file_name)

    #print(f"Blob {blob_name} downloaded to {destination_file_name}.")

def load_config_from_file(file_path):
    """Loads a yaml config file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def get_config(bucket_name, blob_name, temp_file_path='config.yaml'):
    """Download the blob and load the config."""
    global current_config  # declare the global variable inside the function

    download_blob_from_gcs(bucket_name, blob_name, temp_file_path)
    new_config = load_config_from_file(temp_file_path)

    # If the config is different from the current config, update it
    if new_config != current_config:
        current_config = new_config

    return current_config



def upload_blob_to_gcs(bucket_name, source_file_name, destination_blob_name):
    # Get GCS credentials from Streamlit secrets
    gcs_credentials = service_account.Credentials.from_service_account_info(st.secrets["gcs"])

    # Create a client using these credentials
    storage_client = storage.Client(credentials=gcs_credentials)

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
