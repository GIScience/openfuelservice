import json
import ntpath
import os
import shutil
import time
import zipfile
from pathlib import Path
from xml.dom.minidom import parseString
from xmlrpc import client

import requests
from deepmerge import always_merger
from xlrd import open_workbook, XLRDError

from openfuelservice.server import temp_folder, file_folder


def unzip_download(source_file_path: Path, destination_folder: Path) -> []:
    files = []
    curr_dir = os.getcwd()
    os.chdir(source_file_path.parent)
    filename = source_file_path.name
    try:
        if zipfile.is_zipfile(filename):
            # Prepare the data to a processable xls file
            open_zip = zipfile.ZipFile(source_file_path, 'r')
            zip_files = open_zip.filelist
            os.chdir(destination_folder.absolute())
            # Extract every file in the zip
            for zip_file in zip_files:
                # Get the byte data
                file_data = open_zip.read(zip_file)
                # Write the byte data to a new file
                # --> That way a complex extract folder structure is omitted
                filename = zip_file.filename
                files.append(destination_folder.joinpath(filename))
                with open(filename, 'wb') as output:
                    output.write(file_data)
            open_zip.close()
            os.chdir(curr_dir)
            return files
        else:
            os.chdir(curr_dir)
            return list
        pass
    except FileNotFoundError:
        print("Couldn't open or unzip " + source_file_path.__str__())


def unzip_shp_file(zip_file: zipfile, source_folder: Path, destination_folder: Path):
    file = ""
    curr_dir = os.getcwd()
    os.chdir(source_folder.absolute())
    try:
        if zip_file.rsplit('.', 1)[-1] == 'zip':
            # Prepare the data to a processable xls file
            open_zip = zipfile.ZipFile(zip_file, 'r')
            zip_files = open_zip.filelist
            os.chdir(destination_folder.absolute())
            # Extract every file in the zip
            for zip_file in zip_files:
                # Get the byte data
                file_data = open_zip.read(zip_file)
                # Write the byte data to a new file
                # --> That way a complex extract folder structure is omitted
                filename = zip_file.filename
                if filename.rsplit('.', 1)[-1] == 'shp':
                    file = filename
                with open(filename, 'wb') as output:
                    output.write(file_data)
            open_zip.close()
            os.chdir(curr_dir)
            return file
        else:
            os.chdir(curr_dir)
            return ""
        pass
    except FileNotFoundError:
        print("Couldn't open or unzip " + zip_file)


def copy_file_to_temp(filename: str) -> Path:
    """
    Copies a file exclusively from the files folder to the temp folder.
    A fast and reliable way to move files internally.
    :param filename: The actual filename. File must be present in the files folder!
    :return: The file path
    """
    try:
        shutil.copyfile(file_folder.joinpath(filename), temp_folder.joinpath(filename))
        return temp_folder.joinpath(filename)
    except FileNotFoundError as err:
        print(err)


def clean_directory(directory_path: Path):
    """
Cleans the given directory.

    :param directory_path: Path to the directory
    """
    try:
        for p in directory_path.iterdir():
            try:
                if p.is_file():
                    os.remove(p.as_posix())
                elif p.is_dir():
                    shutil.rmtree(p)
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass


def create_directory(directory_path: str) -> Path:
    """
Creates the desired directory

    :param directory_path: Path for the directory location
    """
    try:
        path = Path(directory_path)
        path.mkdir(exist_ok=True)
        return path
    except OSError as err:
        print(err)


def file_from_zip(file_name: str, zip_file: object) -> Path:
    """
Searches a zip file for the given file_name and extracts it to the temp folder

    :param file_name: The filename to be extracted from the zip
    :param zip_file: The zip file
    :return: Returns complete file path leading the file lying in temp
    :rtype: str
    """
    if zipfile.is_zipfile(zip_file):
        # Prepare the data to a processable xls file
        open_zip = zipfile.ZipFile(zip_file, 'r')
        zip_infos = open_zip.filelist
        # Check every file in the zip
        for zip_info in zip_infos:
            # Check if the zip file equals the desired dataset
            if file_name in zip_info.filename:
                # if so, get the byte data
                file_data = open_zip.read(zip_info)
                # Write the byte data to a new file
                # --> That way a complex extract folder structure is omitted
                with open(temp_folder.joinpath(file_name), 'wb') as output:
                    output.write(file_data)
                break
            open_zip.close()
        return temp_folder.joinpath(file_name)
    else:
        return Path('')


def download_file_with_name(url: str, file_name: str):
    """Downloads and stores a file. It will always be stored in the temp folder!!!


        :param url: Url in String format
        :return: Absolute system path to the downloaded file or None
        :rtype: str
        """
    create_directory(temp_folder)
    os.chdir(temp_folder)
    response = get_response(url)
    try:
        with open(file_name, 'wb') as output:
            output.write(response.content)
        return temp_folder.joinpath(file_name)
    except requests.ConnectionError as err:
        print("Couldn't download from url: {}".format(url))
        print(err)


def download_file(url: str) -> Path:
    """Downloads and stores a file. It will always be stored in the temp folder!!!


    :param url: Url in String format
    :return: Absolute system path to the downloaded file or None
    :rtype: str
    """
    create_directory(temp_folder)
    os.chdir(temp_folder)
    resp = get_response(url)
    filename = url.rsplit('/', 1)[-1]
    try:
        with open(filename, 'wb') as output:
            output.write(resp.content)
        return temp_folder.joinpath(filename)
    except requests.ConnectionError as err:
        print("Couldn't download from url: {}".format(url))
        print(err)


def get_response(url: str, timeout: int = 10) -> requests.Response:
    """
    Function to get content from an url.
    It's purpose is to control a global timeout value and to make sure threaded crawling isn't getting out of hand!
    For the "not getting out of hand part" every timed out get request needs to wait 10 secs to start again.

    :param url: Url to download data from
    :return: Returns the usual response
    :rtype: requests.Response
    :type timeout: int
    """
    try:
        response = requests.request("GET", url, timeout=timeout)
        return response
    except (TimeoutError, Exception) as err:
        if err == TimeoutError:
            time.sleep(10)
            print(err)
            get_response(url=url)
        elif err == Exception:
            print(err)


def get_header_link(response: requests.Response, first_url=False, next_url=False, last_url=False):
    link = ""
    try:
        if next_url:
            link = response.links.get('next')['url']
            return link
        elif first_url:
            link = response.links.get('first')['url']
            return link
        elif last_url:
            link = response.links.get('last')['url']
            return link
    except Exception:
        pass
    return None


def delete_file(file: Path):
    if file.is_file():
        try:
            file.unlink()
        except FileNotFoundError as err:
            print(err)


def find_values_in_json(id: str, json_repr: str):
    def val(node):
        # Searches for the next Element Node containing Value
        e = node.nextSibling
        while e and e.nodeType != e.ELEMENT_NODE:
            e = e.nextSibling
        return (e.getElementsByTagName('string')[0].firstChild.nodeValue if e
                else None)
        # parse the JSON as XML

    foo_dom = parseString(client.dumps((json.loads(json_repr),)))
    # and then search all the name tags which are P1's
    # and use the val user function to get the value
    return [val(node) for node in foo_dom.getElementsByTagName('name')
            if node.firstChild.nodeValue in id]


def get_linked_json_content(url: str) -> dict:
    """
    The function will read the header rel links returned by the response and crawl until it reaches the end.
    The responses are extracted as json and after crawling returned --> combined of course!
    This is not designed for huge crawling --> Because it will only run on a single thread!
    The function is designed to work with json responses -> Measurements download.

    :param url:
    :return:
    """
    # TODO finish here. Take the html header links in account!
    complete_content = dict()
    response = get_response(url=url)
    always_merger.merge(complete_content, response.json())
    complete_content.update(response.json())
    next_url = get_header_link(response=response, next_url=True)
    last_url = get_header_link(response=response, last_url=True)
    if next_url and last_url:
        while next_url:
            response = get_response(url=next_url)
            always_merger.merge(complete_content, response.json())
            next_url = get_header_link(response=response, next_url=True)
        response = get_response(last_url)
        always_merger.merge(complete_content, response.json())
    return complete_content


def test_xls(file: object) -> bool:
    """Tests whether the file is from format xls or not

    :param file: xls File
    :return: Returns True or False
    :rtype: bool
    """
    try:
        book = open_workbook(file)
        return True
    except XLRDError as e:
        print(e)
        return False


def get_basename(filepath: object) -> str:
    """
    If a file was provided with a full path this function returns only the basename (filename).
    The reason for this function is it's os independency!

    :param filepath: File path
    :return: Only the filename
    """
    head, tail = ntpath.split(filepath)
    return tail or ntpath.basename(head)
