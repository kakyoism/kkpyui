import os.path as osp
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time
# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/..'))
# import kkpyui as ui
# import kkpyutil as util
from kkpyui import ProgressPrompt, ProgressEvent, ErrorEvent


def run_task(progress_prompt):
    progress_prompt.send_progress("Task", 0, "Starting...")
    time.sleep(3)  # Simulate work
    progress_prompt.send_progress("Task", 100, "Completed!")
    progress_prompt.term()

def start_background_task():
    progress_prompt = ProgressPrompt(root, determinate=False)
    progress_prompt.init("Indeterminate Task")
    threading.Thread(target=run_task, args=(progress_prompt,), daemon=True).start()
    progress_prompt.poll()

root = tk.Tk()
root.title("ProgressPrompt Demo: Indeterminate")
root.geometry("300x200")

start_button_indeterminate = ttk.Button(root, text="Start Indeterminate Task", command=start_background_task)
start_button_indeterminate.pack(pady=10)

root.mainloop()
