#!/usr/bin/python

import dropbox
import json
import os
import subprocess
import time

CONF_PATH = "conf.json"

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


def process_picture(path):
    print "Processing picture"
    print "----- convert start -----"
    print subprocess.check_output(["convert", path, "-rotate", "-90", path])
    print "----- convert end -----"
    print "Picture processed and saved to: %s" % path


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


def delete_local_picture(path):
    print "Deleting local picture"
    print "----- rm start -----"
    print subprocess.check_output(["rm", path])
    print "----- rm end -----"
    print "Done deleting local picture"
    return

def main():
    load_config(CONF_PATH)
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    try:
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError as e:
        print "ERROR: Invalid access token; try re-generating an access token from the Dropbox dev website."
        return False
    while True:
        raw_input("press ENTER to take a picture")
        pass
        path = take_picture()
        process_picture(path)
        success, err = upload_picture(dbx, path)
        if success:
            print "Picture uploaded from: %s" % path
            delete_local_picture(path)
        else:
            print "Couldn't upload from %s due to %s" % (path, err)


if __name__=="__main__":
    main()
