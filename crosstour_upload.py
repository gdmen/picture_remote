#!/usr/bin/python

import dropbox
import json
import logging
import os
from Queue import Queue
import subprocess
from threading import Thread
import time

CONF_PATH = "conf.json"

CROSSTOUR_PATH = ""
DROPBOX_ACCESS_TOKEN = ""
log_file_name = "crosstour_camera_%s.log" % time.strftime("%Y%m%d%H%M%S")
logging.basicConfig(filename=os.path.join(".", log_file_name), level=logging.INFO)


def dropbox_upload(dbx, path):
    f = open(path)
    file_size = os.path.getsize(path)
    dest_path = "/" + os.path.basename(path)

    CHUNK_SIZE = 32 * 1024 * 1024

    if file_size <= CHUNK_SIZE:
        logging.info(dbx.files_upload(f.read(), dest_path))
    else:
        upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                   offset=f.tell())
        commit = dropbox.files.CommitInfo(path=dest_path)
        while f.tell() < file_size:
            if ((file_size - f.tell()) <= CHUNK_SIZE):
                logging.info(dbx.files_upload_session_finish(
                    f.read(CHUNK_SIZE),
                    cursor,
                    commit))
            else:
                dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                cursor.session_id,
                                                cursor.offset)
                cursor.offset = f.tell()


def load_config(path):
    global CROSSTOUR_PATH
    global DROPBOX_ACCESS_TOKEN
    logging.info("Loading config")
    with open(path) as f:    
        data = json.load(f)
    CROSSTOUR_PATH = data["crosstour_path"]
    DROPBOX_ACCESS_TOKEN = data["dropbox_access_token"]
    logging.info("Done loading config")


def upload_picture(dbx, path):
    """Upload a file.
    Return a boolean indicating success.
    """
    logging.info("Uploading picture")
    try:
        dropbox_upload(dbx, path)
    except Exception as e:
        return False, e
    return True, None


def handle_queue(queue, dbx):
    while True:
        path = queue.get()
        logging.info("Processing queue element %s" % path)
        success, err = upload_picture(dbx, path)
        if success:
            logging.info("Picture uploaded from: %s" % path)
            delete_local_picture(path)
        else:
            logging.info("Couldn't upload from %s due to %s" % (path, err))
            if type(err) is dropbox.exceptions.ApiError:
                logging.info("Re-queuing %s" % path)
                queue.put(path)
                continue
        queue.task_done()


def delete_local_picture(path):
    logging.info("Deleting local picture %s" % path)
    logging.info("----- rm start -----")
    logging.info(subprocess.check_output(["rm", path]))
    logging.info("----- rm end -----")
    logging.info("Done deleting local picture %s" % path)
    return


def find_car_videos():
    global CROSSTOUR_PATH
    logging.info("Finding car videos in %s" % CROSSTOUR_PATH)
    try:
        files = subprocess.check_output(["ls", CROSSTOUR_PATH]).split("\n")
        files = [os.path.join(CROSSTOUR_PATH, f) for f in files if len(f) > 0]
    except Exception as e:
        logging.info("Failed to ls %s due to %s" % (CROSSTOUR_PATH, e))
        return []
    return files


def main():
    logging.info("starting...")
    load_config(CONF_PATH)
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    try:
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError as e:
        logging.info("ERROR: Invalid access token; try re-generating an access token from the Dropbox dev website.")
        return False
    logging.info("connected to dropbox")

    # Start upload thread
    upload_queue = Queue(maxsize=0)
    upload_thread = Thread(target=handle_queue, args=(upload_queue, dbx))
    upload_thread.setDaemon(True)
    upload_thread.start()

    delay = 1
    while True:
        if not upload_queue.empty():
            time.sleep(delay * 100)
            continue
        paths = find_car_videos()
        for path in paths:
            upload_queue.put(path)
            logging.info("Enqueuing %s" % path)
            logging.info("Queue length %d" % upload_queue.qsize())
        time.sleep(delay)


if __name__=="__main__":
    main()
