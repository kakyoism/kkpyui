"""
DEMO: Form-based UI for oneshot action
with builtin support for:
- model-view-controller pattern
- two-pane layout for 2-layer navigation
- per-entry help text
- per-entry and global resetting to default
- loading/saving presets
- progress bar
- keyboard shortcuts for running and quitting
"""
import copy
import json
import os.path as osp
import sys
import time

# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/../src'))
import kkpyui as ui
import kkpyutil as util


class Controller(ui.FormController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt = ui.Prompt()

    def on_open_help(self):
        util.alert('Dev: Just use it! Trust yourself and the log!')

    def on_open_log(self):
        log = util.find_log_path(self.prompt.logger)
        if not log:
            return
        util.open_in_browser(log)

    def on_report_issue(self):
        self.prompt.info('Dev: It\'s not a bug, it\'s a feature!')

    def run_task(self):
        """
        - override this in app
        - run in background thread to avoid blocking UI
        """
        self.start_progress()
        for p in range(101):
            # Simulate a task
            time.sleep(0.01)
            self.set_progress('/processing', p, 'Processing ...')
            if self.is_scheduled_to_stop():
                self.stop_progress()
                return
        self.stop_progress()
        out = vars(self.get_latest_model())
        self.model['export'] = osp.join(util.get_platform_tmp_dir(), 'form.out.json')
        util.save_json(self.model['export'], out)
        dmp = json.dumps(self.model, indent=2)
        self.prompt.info(f'{dmp}', confirm=True)
        self.update_view()


def main():
    ui.Globals.root = ui.Root('Form Demo: Character Design', (800, 600))
    form = ui.Form(ui.Globals.root, ['profile', 'plot', 'output'])
    ctrlr = Controller(form)
    ui.Globals.root.set_controller(ctrlr)
    ui.Globals.root.bind_events()
    menu = ui.FormMenu(ui.Globals.root, ctrlr)
    # Adding widgets to pages
    pg1 = form.pages['profile']
    pg2 = form.pages['plot']
    pg3 = form.pages['output']
    name_wgt = ui.TextEntry(pg1, 'name', "Name", "Robin Sena", "text widget.")
    age_wgt = ui.IntEntry(pg1, 'age', "Age", 15, "integer widget", True, (0, float('inf')))
    height_wgt = ui.FloatEntry(pg1, 'height', "Height (m)", 1.68, "float widget", True, (0.0, 2.0), 0.01, 2)
    weight_wgt = ui.FloatEntry(pg1, 'weight', "Weight (kg)", 51, "float widget", True, (50.2, 70.3), 0.1, 1)
    gender_wgt = ui.SingleOptionEntry(pg1, 'gender', "Gender", ["Male", "Female", "[Secret]"], "Female", "option widget")
    protagonist_wgt = ui.BoolEntry(pg1, 'is_protagonist', "Protagonist", True, "checkbox widget")
    bio_widget = ui.TextEntry(pg1, 'bio', "Bio", """Robin Sena (瀬名 ロビン, Sena Robin) is a soft-spoken 15-year-old Hunter and craft-user with pyrokinetic abilities. She was raised in a convent in Italy-(where she was taught how to use and control her
    craft in hunting down Witches) before she was sent to the STN-J to gather information for the Solomon administration; even though she was born in Japan, she had moved to Tuscany when she was still very young. Her witch powers allow her to channel her energy into shields capable of blocking solid matter and crafts, magical powers. -- Wikipedia""", 'text widget.')
    occupation_wgt = ui.MultiOptionEntry(pg2, 'occupation', 'Occupation', ['Lead', 'Warrior', 'Wizard', 'Detective', 'Hacker', 'Clerk'], ['Wizard', 'Detective'], "option widget")
    export_wgt = ui.ReadOnlyPathEntry(pg3, 'export', 'Export to File', '', 'Path to exported file')
    action_bar = ui.FormActionBar(ui.Globals.root, ctrlr)
    progress_bar = ui.ProgressBar(ui.Globals.root, ui.Globals.progressQueue)
    progress_bar.poll()
    ui.Globals.root.mainloop()


if __name__ == "__main__":
    main()
