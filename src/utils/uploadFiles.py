import os
from pathlib import Path
import time
from azure.core.exceptions import ServiceResponseError


import mimetypes
from datetime import datetime, timedelta

from azure.storage.blob import BlobServiceClient, ContentSettings 
from azure.storage.blob import generate_account_sas, ResourceTypes, AccountSasPermissions

root_dir = 'data'


def create_container(container_name: str, blob_service_client: BlobServiceClient):
    blob_container_client = blob_service_client.get_container_client(container_name)
    try:
        blob_container_client.get_container_properties()
    except:
        blob_container_client.create_container()


def upload_blob(local_file_path: str, blob_service_client: BlobServiceClient, container_name: str):
    dir_list = list(Path(local_file_path).parts)
    container_name = container_name
    blob_name = os.path.join(*dir_list)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        blob_properties = blob_client.get_blob_properties()
    except:
        blob_properties = None

    # Skip if the blob already exists
    if blob_properties:
        return

    try:
        with open(file=local_file_path, mode='rb') as f:
            blob_client = blob_service_client.get_blob_client(container_name, blob_name)
            _, extension = os.path.splitext(local_file_path)
            # Get the mime_type based on file extension
            mime_type = mimetypes.types_map.get(extension, 'application/octet-stream')
            content_settings = ContentSettings(content_type=mime_type)

            # Adding the timeout parameter to the upload_blob call
            blob_client.upload_blob(data=f, content_settings=content_settings, timeout=300)

    except (ServiceResponseError, TimeoutError) as e:
        # Log the error and skip the file
        print(f"Timeout or connection error while uploading {local_file_path}. Skipping file.")


def upload_all(account_key, account_name, account_url, root_dir, container_name):
    sas_token = generate_account_sas(
        account_name=account_name,
        account_key=account_key,
        resource_types=ResourceTypes(object=True, container=True),
        permission=AccountSasPermissions(read=True, write=True, create=True, delete=True, list=True),
        expiry=datetime.utcnow() + timedelta(days=30)
    )
    b_s_c = BlobServiceClient(account_url=account_url,
                              credential=sas_token)
    # Iterate through the root directory and create containers and blobs
    for root, dirs, files in os.walk(root_dir):
        if root == root_dir and len(dirs) == 0:
            print("No containers specified.")
            break
        elif len(files) > 0:
            for file in files:
                upload_blob(os.path.join(root, file), b_s_c, container_name)