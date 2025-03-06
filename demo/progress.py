import os.path as osp
import sys
import tkinter as tk
import threading
import time

# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/..'))
# import kkpyui as ui
# import kkpyutil as util
from kkpyui import ProgressPrompt, ProgressEvent, ErrorEvent


def background_task(progress_prompt):
    """
    Simulated background task that updates the progress.
    """
    for i in range(101):
        if progress_prompt.abortEvent.is_set():
            break  # Stop if user cancels
        progress_prompt.send_progress("Task", i, f"Processing {i}%")
        time.sleep(0.1)  # Simulate work
    progress_prompt.term()  # Close the progress prompt when done


def start_task():
    """
    Starts the background task in a separate thread.
    """
    progress_event = ProgressEvent()
    abort_event = threading.Event()
    error_event = ErrorEvent()

    progress_prompt = ProgressPrompt(root, determinate=True, prog_evt=progress_event, abort_evt=abort_event, error_evt=error_event)
    progress_prompt.init("Running Background Task")

    thread = threading.Thread(target=background_task, args=(progress_prompt,))
    thread.start()
    progress_prompt.poll()


# Create main application window
root = tk.Tk()
root.title("ProgressPrompt Demo: Determinate")
root.geometry("300x200")

start_button = tk.Button(root, text="Start", command=start_task)
start_button.pack(pady=50)

root.mainloop()
