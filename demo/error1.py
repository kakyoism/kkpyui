import os.path as osp
import sys
import tkinter as tk
import threading
import time
import traceback
from tkinter import ttk
import types

# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/..'))
import kkpyui as ui
import kkpyutil as util


def run_task(progress_prompt):
    """
    Simulated background task that updates the progress.
    """
    try:
        for i in range(101):
            if progress_prompt.abortEvent.is_set():
                break  # Stop if user cancels
            if i == 10:  # Simulate an error at 10% progress
                raise ValueError(f"Simulated error at {i}% progress")
            time.sleep(0.01)  # Simulate work
            progress_prompt.send_progress("Task", i, f"Processing {i}%")
    except Exception as e:
        # Log the error and show the error prompt
        progress_prompt.errorEvent.set_error(e, traceback.format_exc())

def start_background_task():
    """
    Starts the background task in a separate thread.
    """
    sync = types.SimpleNamespace(
        progEvent=ui.ProgressEvent(),
        abortEvent=threading.Event(),
        errorEvent=ui.ErrorEvent(),
    )
    help = types.SimpleNamespace(
        reporter=lambda exc, cookie: util.alert(f"{exc=}; {cookie=}; sent to someone@dev.com", 'report'),
        cookie=types.SimpleNamespace(log='error.log', dump='error.dump'),
        helper={ValueError: "Please check the input values."},
    )
    progress_prompt = ui.ProgressPrompt(root, determinate=True, sync=sync, help=help)
    progress_prompt.init("Running Background Task")

    thread = threading.Thread(target=run_task, args=(progress_prompt,))
    thread.start()
    progress_prompt.poll()


# Create main application window
root = tk.Tk()
root.title("ProgressPrompt Demo: Determinate")
root.geometry("300x200")

start_button = tk.Button(root, text="Start Determinate Task", command=start_background_task)
start_button.pack(pady=50)

root.mainloop()