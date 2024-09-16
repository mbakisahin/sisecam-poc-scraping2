import zlib
import zipfile
import os
import shutil

"""
Burası tam bir mass ama gece ikide biten bir işin parçası

Respect += 1
Emek += 1
Uykusuzluk += 1
para -= (dışardan söylenen yemek ücreti)
"""


def copy_raw_data(source_dir, dest_dir):
    # Create the destination directory if it doesn't exist
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Iterate through each website folder in the source directory
    for website_folder in os.listdir(source_dir):
        website_path = os.path.join(source_dir, website_folder)
        if os.path.isdir(website_path):
            dest_website_path = os.path.join(dest_dir, website_folder)
            # Create the destination website folder
            os.makedirs(dest_website_path, exist_ok=True)
            # Iterate through each subfolder (keyword folders) in the website folder
            for keyword_folder in os.listdir(website_path):
                keyword_path = os.path.join(website_path, keyword_folder)
                if os.path.isdir(keyword_path):
                    # Create the corresponding keyword folder in the destination
                    dest_keyword_path = os.path.join(dest_website_path, keyword_folder)
                    os.makedirs(dest_keyword_path, exist_ok=True)

def zip_files_with_same_names(source_dir, dest_dir):
    filenames = dict()
    destination_path_list = list()
    # Iterate through each website folder in the source directory
    for website_folder in os.listdir(source_dir):
        website_path = os.path.join(source_dir, website_folder)
        if os.path.isdir(website_path):
            # Iterate through each keyword folder in the website folder
            for keyword_folder in os.listdir(website_path):
                keyword_path = os.path.join(website_path, keyword_folder)
                if os.path.isdir(keyword_path):
                    # Create the corresponding destination folder in raw_copy directory
                    dest_keyword_path = os.path.join(dest_dir, website_folder, keyword_folder)
                    os.makedirs(dest_keyword_path, exist_ok=True)

                    # Collect filenames without extension across text, json, and pdf folders

                    text_folder_path = os.path.join(keyword_path, 'text')
                    text_files = os.listdir(text_folder_path)
                    for file in text_files:
                        filenames[os.path.splitext(file)[0]] = list()
                        destination_path_list.append(dest_keyword_path)
                    extensions = ['.txt', '.pdf', '.json', '.json']
                    for index_, extension in enumerate(['text', 'pdf', 'json', 'metadata']):
                        current_extension_directory = os.path.join(keyword_path, extension)

                        for file in filenames.keys():
                            temp_file = file + extensions[index_]
                            if temp_file in os.listdir(current_extension_directory) or 'metadata_' + temp_file in os.listdir(current_extension_directory):
                                if extension == 'metadata':
                                    file_ = 'metadata_' + file
                                    will_append_file_name = file_ + extensions[index_]
                                    path_to_add = os.path.join(current_extension_directory, will_append_file_name)
                                    filenames[file].append(path_to_add)
                                else:
                                    will_append_file_name = file + extensions[index_]
                                    path_to_add = os.path.join(current_extension_directory, will_append_file_name)
                                    filenames[file].append(path_to_add)


    return filenames, destination_path_list

def compress(file_names, path_to_write, zip_name):
    # Select the compression mode ZIP_DEFLATED for compression
    # or zipfile.ZIP_STORED to just store the file
    compression = zipfile.ZIP_DEFLATED

    # create the zip file first parameter path/name, second mode
    zf = zipfile.ZipFile(os.path.join(path_to_write, zip_name), mode="w")
    try:
        for file_name in file_names:
            # Add file to the zip file
            # first parameter file to zip, second filename in zip
            zf.write(file_name, file_name.split('/')[-1], compress_type=compression)

    except FileNotFoundError:
        print("An error occurred")
    finally:
        # Don't forget to close the file!
        zf.close()