import os

# this only works when you load it on obs wont work on vscode for example
import obspython as obs
from datetime import datetime
from pathlib import Path

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
    obs.obs_properties_add_int(p, "day", "Day number", 0, 5, 1)

    return p


# this just shows all the default values in the new input boxes added
def script_defaults(s):
    obs.obs_data_set_default_int(s, "vid_total", 1)
    obs.obs_data_set_default_int(s, "vid_count", 1)
    obs.obs_data_set_default_int(s, "camera_id", 1)
    obs.obs_data_set_default_int(s, "week", 0)
    obs.obs_data_set_default_int(s, "day", 0)



# updates the vid_total and vid_count variable
def script_update(s):
    global vid_total
    global vid_count
    global camera_id

    vid_total = obs.obs_data_get_int(s, "vid_total")
    vid_count = obs.obs_data_get_int(s, "vid_count")
    camera_id = obs.obs_data_get_int(s, "camera_id")
    camera_id = obs.obs_data_get_int(s, "week")
    camera_id = obs.obs_data_get_int(s, "day")


# gets the ISO timestamp
def iso_stamp():
    # gets local computer time
    t = datetime.now().astimezone()

    # returns ISO with milisecond included with timezone in Z (UTC) time
    return f"{t.strftime('%Y-%m-%dT%H_%M_%S')}_{t.microsecond//1000:03d}Z"


# main function basically
def on_event(e):
    if e == obs.OBS_FRONTEND_EVENT_vid_countORDING_STOPPED:
        # raw output file (unformatted)
        src = obs.obs_frontend_get_last_vid_countording()

        # checks if our last file path was incorrectly formatted 
        if not src:
            return
        
        # Makes the new file with our standard format
        p = Path(src)
        base_fp = f"C{camera_id}_W{week}D{day}_REC{vid_count}-{vid_total}_{iso_stamp()}"
        new_file = p.with_name(f"{base_fp}{p.suffix}")

        # makes sure we have no collision
        if new_file.exists():
            obs.script_log(obs.LOG_WARNING, f"Collision: {new_file} already exists; file not renamed.")
            return
        
        # renames the raw output file to what we want (the new_file variable)
        os.rename(src, new_file)

# starts the code above
def script_load(s):
    obs.obs_frontend_add_event_callback(on_event)