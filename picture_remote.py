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

WEBCAM_RESOLUTION = ""
DROPBOX_ACCESS_TOKEN = ""
log_file_name = "picture_remote_%s.log" % time.strftime("%Y%m%d%H%M%S")
logging.basicConfig(filename=os.path.join(".", log_file_name), level=logging.INFO)

def load_config(path):
    global WEBCAM_RESOLUTION, DROPBOX_ACCESS_TOKEN
    logging.info("Loading config")
    with open(path) as f:    
        data = json.load(f)
    WEBCAM_RESOLUTION = data["webcam_resolution"]
    DROPBOX_ACCESS_TOKEN = data["dropbox_access_token"]
    logging.info("Done loading config")


def take_picture():
    logging.info("Taking picture")
    time_str = time.strftime("%Y%m%d-%H%M%S")
    path = "%s.png" % time_str
    logging.info("----- fswebcam start -----")
    logging.info(subprocess.check_output(["fswebcam","-r",WEBCAM_RESOLUTION,"--no-banner",path]))
    logging.info("----- fswebcam end -----")
    logging.info("Picture saved to: %s" % path)
    return path


def transform_picture(path):
    logging.info("Transforming picture")
    logging.info("----- convert start -----")
    logging.info(subprocess.check_output(["convert", path, "-rotate", "-90", path]))
    logging.info("----- convert end -----")
    logging.info("Picture transformed and saved to: %s" % path)


def upload_picture(dbx, path):
    """Upload a file.
    Return a boolean indicating success.
    """
    logging.info("Uploading picture")
    with open(path, "rb") as f:
        try:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            dbx.files_upload(f.read(), "/" + os.path.basename(path), mode=dropbox.files.WriteMode("overwrite"))
        except dropbox.exceptions.ApiError as err:
            return False, err
    return True, None


def handle_queue(queue, dbx):
    while True:
        path = queue.get()
        logging.info("Processing queue element %s" % path)
        transform_picture(path)
        success, err = upload_picture(dbx, path)
        if success:
            logging.info("Picture uploaded from: %s" % path)
            delete_local_picture(path)
        else:
            logging.info("Couldn't upload from %s due to %s" % (path, err))
        queue.task_done()


def delete_local_picture(path):
    logging.info("Deleting local picture %s" % path)
    logging.info("----- rm start -----")
    logging.info(subprocess.check_output(["rm", path]))
    logging.info("----- rm end -----")
    logging.info("Done deleting local picture %s" % path)
    return


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

    # Loop on stdin
    while True:
        raw_input("press ENTER to take a picture\n")
        path = take_picture()
        upload_queue.put(path)
        logging.info("Enqueuing %s" % path)
        logging.info("Queue length %d" % upload_queue.qsize())


if __name__=="__main__":
    main()
