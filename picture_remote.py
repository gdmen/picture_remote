#!/usr/bin/python

import dropbox
import json
import os
from Queue import Queue
import subprocess
from threading import Thread
import time

CONF_PATH = "conf.json"

UPLOAD_BUFFER_SIZE = 4

WEBCAM_RESOLUTION = ""
DROPBOX_ACCESS_TOKEN = ""


def load_config(path):
    global WEBCAM_RESOLUTION, DROPBOX_ACCESS_TOKEN
    print "Loading config"
    with open(path) as f:    
        data = json.load(f)
    WEBCAM_RESOLUTION = data["webcam_resolution"]
    DROPBOX_ACCESS_TOKEN = data["dropbox_access_token"]
    print "Done loading config"


def take_picture():
    print "Taking picture"
    time_str = time.strftime("%Y%m%d-%H%M%S")
    path = "%s.png" % time_str
    print "----- fswebcam start -----"
    print subprocess.check_output(["fswebcam","-r",WEBCAM_RESOLUTION,"--no-banner",path])
    print "----- fswebcam end -----"
    print "Picture saved to: %s" % path
    return path


def transform_picture(path):
    print "Transforming picture"
    print "----- convert start -----"
    print subprocess.check_output(["convert", path, "-rotate", "-90", path])
    print "----- convert end -----"
    print "Picture transformed and saved to: %s" % path


def upload_picture(dbx, path):
    """Upload a file.
    Return a boolean indicating success.
    """
    print "Uploading picture"
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
        print "Processing queue element %s" % path
        transform_picture(path)
        success, err = upload_picture(dbx, path)
        if success:
            print "Picture uploaded from: %s" % path
            delete_local_picture(path)
        else:
            print "Couldn't upload from %s due to %s" % (path, err)
        queue.task_done()


def delete_local_picture(path):
    print "Deleting local picture %s" % path
    print "----- rm start -----"
    print subprocess.check_output(["rm", path])
    print "----- rm end -----"
    print "Done deleting local picture %s" % path
    return

def main():
    load_config(CONF_PATH)
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    try:
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError as e:
        print "ERROR: Invalid access token; try re-generating an access token from the Dropbox dev website."
        return False

    # Start upload thread
    upload_queue = Queue(maxsize=0)
    upload_thread = Thread(target=handle_queue, args=(upload_queue, dbx))
    upload_thread.setDaemon(True)
    upload_thread.start()

    # Loop on stdin
    upload_buffer = []
    while True:
        raw_input("press ENTER to take a picture\n")
        path = take_picture()
        print "Buffering %s" % path
        upload_buffer.append(path)
        print "Buffer length %d" % len(upload_buffer)
        if len(upload_buffer) >= UPLOAD_BUFFER_SIZE:
            for path in upload_buffer:
                print "Enqueuing %s" % path
                upload_queue.put(path)
                print "Queue length %d" % upload_queue.qsize()
            upload_buffer = []


if __name__=="__main__":
    main()
