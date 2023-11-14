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
import os.path as osp
import sys
import time

# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/../src'))
import kkpyui as ui


class MyController(ui.FormController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run_background(self):
        """
        - override this in app
        - run in background thread to avoid blocking UI
        """
        ui.Globals.progressQueue.put(('/start', 0, 'Processing ...'))
        for p in range(101):
            # Simulate a task
            time.sleep(0.01)
            ui.Globals.progressQueue.put(('/processing', p, f'Processing {p}%...'))
        ui.Globals.progressQueue.put(('/stop', 100, 'Completed!'))
        prompt = ui.Prompt()
        prompt.warning('You are calling base class', 'Subclass this!')


def main():
    ui.Globals.root = ui.Root('Form Example', (800, 600))
    form = ui.Form(ui.Globals.root)
    form.layout()
    ctrlr = MyController(form)
    ui.Globals.root.bind_events(ctrlr)
    menu = ui.FormMenu(ui.Globals.root, ctrlr)
    menu.init(ui.Globals.root)
    # Creating groups
    pg1 = ui.Page(form.entryPane, "Group 1")
    pg1.layout()
    pg2 = ui.Page(form.entryPane, "Group 2")
    pg2.layout()
    pg3 = ui.Page(form.entryPane, "Group 3")
    pg3.layout()
    # Adding widgets to groups
    integer_widget = ui.IntEntry(pg1, "Integer Value", 10, "This is an integer value.", (0, 100))
    float_widget = ui.FloatEntry(pg1, "Float Value", 0.5, "This is a float value.", (0.0, 1.0), 0.01, 4)
    option_widget = ui.OptionEntry(pg2, "Options", ["Option 1", "Option 2", "Option 3"], "Option 2", "This is an options widget.")
    checkbox_widget = ui.Checkbox(pg2, "Checkbox", True, "This is a checkbox widget.")
    text_widget = ui.TextEntry(pg3, "Text", "Lorem ipsum dolor sit amet", "This is a text widget.")
    pg1.add([integer_widget, float_widget])
    pg2.add([option_widget, checkbox_widget])
    pg3.add([text_widget])
    form.init([pg1, pg2, pg3])
    form.layout()
    action_bar = ui.FormActionBar(ui.Globals.root, ctrlr)
    action_bar.layout()
    progress_bar = ui.ProgressBar(ui.Globals.root, ui.Globals.progressQueue)
    progress_bar.layout()
    progress_bar.poll()
    ui.Globals.root.mainloop()


if __name__ == "__main__":
    main()
