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
import json
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
        out = self.pack()
        prompt.info(f'{json.dumps(vars(out))}', confirm=True)


def main():
    ui.Globals.root = ui.Root('Form Demo: Character Design', (800, 600))
    form = ui.Form(ui.Globals.root, ['profile', 'plot'])
    ctrlr = MyController(form)
    ui.Globals.root.bind_events(ctrlr)
    menu = ui.FormMenu(ui.Globals.root, ctrlr)
    # Adding widgets to pages
    pg1 = form.pages['profile']
    pg2 = form.pages['plot']
    name_wgt = ui.TextEntry(pg1, "Name", "Robin Sena", "text widget.")
    age_wgt = ui.IntEntry(pg1, "Age", 15, "integer widget", (0, float('inf')))
    height_wgt = ui.FloatEntry(pg1, "Height (m)", 1.68, "float widget", (0.0, 2.0), 0.01, 2)
    weight_wgt = ui.FloatEntry(pg1, "Weight (kg)", 51, "float widget", (50.2, 70.3), 0.1, 1)
    gender_wgt = ui.SingleOptionEntry(pg1, "Gender", ["Male", "Female", "[Secret]"], "Female", "option widget")
    protagonist_wgt = ui.BoolEntry(pg1, "Protagonist", True, "checkbox widget")
    bio_widget = ui.TextEntry(pg1, "Bio", """Robin Sena (瀬名 ロビン, Sena Robin) is a soft-spoken 15-year-old Hunter and craft-user with pyrokinetic abilities. She was raised in a convent in Italy-(where she was taught how to use and control her craft in "
                                          "hunting down Witches) before she was sent to the STN-J to gather information for the Solomon administration; even though she was born in Japan, she had moved to Tuscany when she was still very young. Her witch powers allow her to channel her energy into shields capable of blocking solid matter and crafts, magical powers. However, any use of her power temporarily weakens her eyesight, greatly reducing her accuracy and effectiveness. This problem is solved when she begins to wear glasses. Although she is good-natured, Robin employs her gift with lethal force when necessary to save a life or for the good of others. As the series progresses, her powers increase rapidly until she is labeled dangerous by Solomon and is ordered to be hunted as a witch. It is discovered that Robin is a "Designer Witch" and was created through "Project Robin", a genetic engineering project. Her mother, Maria, had agreed to genetic manipulation and called the unborn Robin "Hope." Robin was designed to give birth to witch kind, what was once called "divinities" in ancient history. Robin was given thousands of years witch kind's memories, the origin of "craft". This enables her to understand the sadness arising from the conflict between humans and witches, in turn allowing her to find a way for humans and witches to peacefully coexist. Amon volunteers to be a watchman who will terminate her if she becomes destructive. She accepts this. After the collapse of the Factory, her fate is unknown. The reactions of the other characters show that she is believed to be alive, but is said to be dead for her own safety. However, after the ending credits it shows that a new hunter arrived at the STN-J, which is actually not a new hunter but Robin herself. She is voiced by Akeno Watanabe in Japanese and Kari Wahlgren in English. -- Wikipedia""", 'text widget.')

    occupation_wgt = ui.MultiOptionEntry(pg2, 'Occupation', ['Lead', 'Warrior', 'Wizard', 'Detective', 'Hacker', 'Clerk'], ['Wizard', 'Detective'], "option widget")
    action_bar = ui.FormActionBar(ui.Globals.root, ctrlr)
    progress_bar = ui.ProgressBar(ui.Globals.root, ui.Globals.progressQueue)
    progress_bar.poll()
    ui.Globals.root.mainloop()


if __name__ == "__main__":
    main()
