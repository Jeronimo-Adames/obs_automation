import os
import time
from datetime import datetime, timezone
from pathlib import Path
import shutil
import obspython as obs

# default values
vid_total = 1
vid_count = 1
camera_id = 1
week = 0
day = 0

# Seema Number for precise timestamping
MEINBERG_DELTA = 1752160362

# adds the input boxes we use to get user-defined values
def script_properties():
    p = obs.obs_properties_create()
    obs.obs_properties_add_int(p, "vid_total", "total video recordings", 1, 100, 1)
    obs.obs_properties_add_int(p, "vid_count", "video recording number", 1, 100, 1)
    obs.obs_properties_add_int(p, "camera_id", "Camera number", 1, 7, 1)
    obs.obs_properties_add_int(p, "week", "Week number", 0, 4, 1)
    obs.obs_properties_add_int(p, "day", "Day number", 1, 5, 1)
    return p

# set initial defaults
def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "vid_total", 1)
    obs.obs_data_set_default_int(settings, "vid_count", 1)
    obs.obs_data_set_default_int(settings, "camera_id", 1)
    obs.obs_data_set_default_int(settings, "week", 0)
    obs.obs_data_set_default_int(settings, "day", 1)

# update global variables when user changes properties
def script_update(settings):
    global vid_total, vid_count, camera_id, week, day

    vid_total   = obs.obs_data_get_int(settings, "vid_total")
    vid_count   = obs.obs_data_get_int(settings, "vid_count")
    camera_id   = obs.obs_data_get_int(settings, "camera_id")
    week        = obs.obs_data_get_int(settings, "week")
    day         = obs.obs_data_get_int(settings, "day")

# returns the ISO stamp at moment of call
def iso_stamp():
    real_time = MEINBERG_DELTA + time.time()
    pst_time  = real_time - (7 * 3600)
    local_time = datetime.fromtimestamp(pst_time, tz=timezone.utc)
    return f"{local_time.strftime('%Y-%m-%dT%H_%M_%S')}_{local_time.microsecond // 1000:03d}-PST"

# frame logging globals
log_file = None
start_time = None
frame_idx = 0

# logs a CSV line each tick
def on_tick():
    global frame_idx
    if not log_file:
        return
    now = time.time()
    relative_ms = (now - start_time) * 1000
    log_file.write(f"{frame_idx},{relative_ms:.3f},{iso_stamp()}\n")
    frame_idx += 1

# logging event: open/close CSV
def logging_event(event):
    global log_file, start_time, frame_idx
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTED:
        output = obs.obs_frontend_get_recording_output()
        if not output:
            return
        settings = obs.obs_output_get_settings(output)
        if not settings:
            obs.obs_output_release(output)
            return
        path = obs.obs_data_get_string(settings, "path")
        obs.obs_data_release(settings)
        obs.obs_output_release(output)

        base = os.path.dirname(path) if path.lower().endswith((".mp4", ".mkv")) else path
        vid_dir = Path(base) / f"W{week}" / f"D{day}" / "vid"
        vid_dir.mkdir(parents=True, exist_ok=True)
        log_dir = vid_dir / "video_log"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_name = f"L{camera_id}_W{week}D{day}_REC{vid_count}-{vid_total}_{iso_stamp()}.csv"
        log_file = open(log_dir / log_name, "w")
        log_file.write("frame,relative_ms,ISO_stamp\n")
        start_time = time.time()
        frame_idx = 0
        obs.timer_add(on_tick, 0)

    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        if log_file:
            obs.timer_remove(on_tick)
            log_file.close()

# move & rename the recording on stop
def formatting_event(event):
    if event != obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        return
    src = obs.obs_frontend_get_last_recording()
    if not src:
        return
    base_dir = Path(src).parent
    vid_dir = base_dir / f"W{week}" / f"D{day}" / "vid"
    vid_dir.mkdir(parents=True, exist_ok=True)
    filename = f"C{camera_id}_W{week}D{day}_REC{vid_count}-{vid_total}_{iso_stamp()}.mp4"
    shutil.move(src, str(vid_dir / filename))

# hook into OBS events
def script_load(settings):
    obs.obs_frontend_add_event_callback(logging_event)
    obs.obs_frontend_add_event_callback(formatting_event)

def script_unload():
    if log_file:
        obs.timer_remove(on_tick)
        log_file.close()
