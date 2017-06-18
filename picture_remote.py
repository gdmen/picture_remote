#!/usr/bin/python

import dropbox
import json
import os
import subprocess
import time

CONF_PATH = "conf.json"

WEBCAM_RESOLUTION = ""
DROPBOX_ACCESS_TOKEN = ""
DBX = None

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


def upload_picture(path):
    global DBX
    """Upload a file.
    Return a boolean indicating success.
    """
    print "Uploading picture"
    if DBX == None:
        DBX = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        try:
            DBX.users_get_current_account()
        except dropbox.exceptions.AuthError as e:
            print "ERROR: Invalid access token; try re-generating an access token from the Dropbox dev website."
            return False
    with open(path, 'rb') as f:
    # We use WriteMode=overwrite to make sure that the settings in the file
    # are changed on upload
        try:
            DBX.files_upload(f.read(), "/" + os.path.basename(path), mode=dropbox.files.WriteMode('overwrite'))
        except dropbox.exceptions.ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and err.error.get_path().error.is_insufficient_space()):
                print "ERROR: Cannot upload; insufficient space."
            elif err.user_message_text:
                print err.user_message_text
            else:
                print err
            return False
    print "Picture uploaded from: %s" % path
    return True


def delete_local_picture(path):
    print "Deleting local picture"
    print "----- rm start -----"
    print subprocess.check_output(["rm", path])
    print "----- rm end -----"
    print "Done deleting local picture"
    return


def main():
    load_config(CONF_PATH)
    while True:
        raw_input("press ENTER to take a picture")
        pass
        path = take_picture()
        process_picture(path)
        if upload_picture(path):
            delete_local_picture(path)
        else:
            print "Couldn't upload."


if __name__=="__main__":
    main()
