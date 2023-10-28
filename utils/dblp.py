import requests
import sys
import os
from datetime import datetime
from hurry.filesize import size
import gzip
import shutil


def download_file(url: str, filename: str):
    """Function to download file"""

    downloaded = False
    with open(filename, "wb") as file:
        response = requests.get(url, stream=True)
        length = response.headers.get("content-length")
        # print(length)
        print(response.status_code)
        if response.status_code != 200:
            print("Connection Error")
            return False
        if length is None:
            print(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "DBLP",
                "Error downloading dataset",
            )
        else:
            download = 0
            length = int(length)
            for data in response.iter_content(
                chunk_size=max(int(length / 1000), 1024 * 1024)
            ):
                download += len(data)
                file.write(data)
                # print(50*download/length)
                done = int(50 * download / length)
                sys.stdout.write(
                    "\r[{}{}] {}/{}".format(
                        "█" * done, "." * (50 - done), size(download), size(length)
                    )
                )
                sys.stdout.flush()
            sys.stdout.write("\n")
            downloaded = True
    return downloaded


def check_latest(url: str, filename: str):
    """Check if the file in the local is the latest"""
    # Check if local file exists
    if not os.path.exists(filename):
        return False

    response = requests.head(url)
    # print(response)
    server_modified_time = response.headers.get("Last-Modified")
    # print(server_modified_time)
    server_modified_time = datetime.strptime(
        server_modified_time, "%a, %d %b %Y %H:%M:%S %Z"
    )

    # Get the last modified time of the local file
    local_modified_time = datetime.fromtimestamp(os.path.getmtime(filename))

    # Compare the last modified times
    return server_modified_time <= local_modified_time


def download_dataset():
    """Function to download the latest dump of the dataset and decompress
    Args:
        None
    Returns:
        None
    """

    dtd_url = "https://dblp.uni-trier.de/xml/dblp.dtd"
    dtd_filename = "dblp.dtd"
    if not check_latest(url=dtd_url, filename=dtd_filename):
        download_file(url=dtd_url, filename=dtd_filename)

    xml_url = "https://dblp.uni-trier.de/xml/dblp.xml.gz"
    xml_filename = "dblp.xml.gz"
    unzip_xml_filename = "dblp.xml"
    if not check_latest(url=xml_url, filename=xml_filename):
        download_file(url=xml_url, filename=xml_filename)
        print("unzipping")
        with gzip.open(xml_filename, "rb") as file_in:
            with open(unzip_xml_filename, "wb") as file_out:
                shutil.copyfileobj(file_in, file_out)
        print("File downloaded and unzipped")
    else:
        if not os.path.exists(unzip_xml_filename):
            print("unzipping")
            with gzip.open(xml_filename, "rb") as file_in:
                with open(unzip_xml_filename, "wb") as file_out:
                    shutil.copyfileobj(file_in, file_out)
            print("File downloaded and unzipped")
        else:
            print("Local File is the latest version")
