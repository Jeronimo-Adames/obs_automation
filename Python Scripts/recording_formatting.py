import os
import time
from datetime import datetime, timezone
from pathlib import Path
import shutil

# this only works when you load it on obs wont work on vscode for example
import obspython as obs

# default values
vid_total = 1
vid_count = 1
camera_id = 1
week = 0
day = 0

# adds the input boxes we use to get input that then changes file name
def script_properties():
    p = obs.obs_properties_create()
    obs.obs_properties_add_int(p, "vid_total", "total video recordings", 1, 100, 1)
    obs.obs_properties_add_int(p, "vid_count", "video recording number", 1, 100, 1)

    # choice of six cameras + backup
    obs.obs_properties_add_int(p, "camera_id", "Camera number", 1, 7, 1)

    # Week and Day Selection (for now only 4 weeks, 5 days in a week, go 0 for testing)
    obs.obs_properties_add_int(p, "week", "Week number", 0, 4, 1)
    obs.obs_properties_add_int(p, "day", "Day number", 1, 5, 1)

    return p

# this just shows all the default values in the new input boxes added
def script_defaults(s):
    obs.obs_data_set_default_int(s, "vid_total", 1)
    obs.obs_data_set_default_int(s, "vid_count", 1)
    obs.obs_data_set_default_int(s, "camera_id", 1)
    obs.obs_data_set_default_int(s, "week", 0)
    obs.obs_data_set_default_int(s, "day", 1)

# updates the vid_total and vid_count variable
def script_update(s):
    global vid_total, vid_count, camera_id, week, day
    vid_total = obs.obs_data_get_int(s, "vid_total")
    vid_count = obs.obs_data_get_int(s, "vid_count")
    camera_id = obs.obs_data_get_int(s, "camera_id")
    week = obs.obs_data_get_int(s, "week")
    day = obs.obs_data_get_int(s, "day")

# Seema Number
MEINBERG_DELTA = 1752160362

# returns the ISO stamp at moment of call
def iso_stamp():
    real_time = MEINBERG_DELTA + time.time()
    pst_time = real_time - (7 * 3600)  # manually subtract 8 hours for PST (Cali Time)
    local_time = datetime.fromtimestamp(pst_time, tz=timezone.utc)  # explicitly UTC
    return f"{local_time.strftime('%Y-%m-%dT%H_%M_%S')}_{local_time.microsecond // 1000:03d}-PST"

# main function for formatting basically
def formatting_event(e):
    if e == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        # get the path of the just-finished recording
        src = obs.obs_frontend_get_last_recording()
        if not src:
            return

        # determine the base directory where OBS saved the file
        base_dir = Path(src).parent

        # make the subfolder W#/D#/vid
        target_dir = base_dir / f"W{week}" / f"D{day}" / "vid"
        target_dir.mkdir(parents=True, exist_ok=True)

        # build the new filename
        filename = f"C{camera_id}_W{week}D{day}_REC{vid_count}-{vid_total}_{iso_stamp()}.mp4"

        # move and rename the recording file
        dest = target_dir / filename
        shutil.move(src, str(dest))

# start listening for events
def script_load(s):
    obs.obs_frontend_add_event_callback(formatting_event)

def script_unload():
    pass
