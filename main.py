from src.saved import ScriptRunner

from src.utils.uploadFiles import upload_all
from src.utils.zipFiles import compress, zip_files_with_same_names, copy_raw_data

from dotenv import load_dotenv

import os

load_dotenv()

#root directory for data
ROOT_DIR = os.path.join(os.path.join(os.getcwd(), 'data'), 'processed')

source_directory = os.path.join(os.path.join(os.getcwd(), 'data'), 'raw')
destination_directory = os.path.join(os.path.join(os.getcwd(), 'data'), 'processed')

# Azure Storage Account Name
ACCOUNT_NAME = os.getenv("account_name")
# Azure Storage Account URL
ACCOUNT_URL = os.getenv("account_url")
# Account Key
ACCOUNT_KEY = os.getenv("account_key")

if __name__ == '__main__':
    script_keywords_file = 'executed_scripts.txt'
    scripts_file_path = 'scripts.txt'

    runner = ScriptRunner(script_keywords_file)
    scripts = runner.read_scripts_from_file(scripts_file_path)
    runner.run_scripts(scripts)

    # copy_raw_data(source_directory, destination_directory)
    #
    # files_, destination = zip_files_with_same_names(source_directory, destination_directory)
    #
    # index = 0
    # for item, values in files_.items():
    #     compress(values, destination[index], item + '.zip')
    #     index += 1
    #
    # os.chdir(ROOT_DIR)
    # for root_dir in os.listdir():
    #     upload_all(ACCOUNT_KEY, ACCOUNT_NAME, ACCOUNT_URL, root_dir, 'ds-sisecam-kalite')