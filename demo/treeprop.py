import os.path as osp
import tkinter as tk
from tkinter import ttk
import sys
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/..'))
import kkpyui as ui
import kkpyutil as util


class DemoTreeModel(ui.TreeModelBase):
    """
    A simple tree model for the demo.
    """
    def __init__(self):
        super().__init__()
        # Example data structure
        self.data = {
            'root': {'name': 'Root', 'tags': [], 'children': ['node1', 'node2']},
            'node1': {'name': 'Node 1', 'tags': [], 'children': ['node1.1', 'node1.2']},
            'node1.1': {'name': 'Node 1.1', 'tags': [], 'children': []},
            'node1.2': {'name': 'Node 1.2', 'tags': [], 'children': []},
            'node2': {'name': 'Node 2', 'tags': [], 'children': ['node2.1']},
            'node2.1': {'name': 'Node 2.1', 'tags': [], 'children': []},
        }

    def get(self, key):
        return self.data.get(key)

    def get_all(self):
        return self.data

    def get_parent_of(self, key):
        return next((k for k, v in self.data.items() if key in v.get('children', [])), None)

    def get_children_of(self, key):
        if key not in self.data:
            return []
        return self.data[key]['children']

    def adapt_to_view(self):
        """
        Dump the model into a group-prop pairs format for the PropertyPane.
        """
        return {
            'General': {
                'name': {'title': 'Name', 'type': 'str', 'default': 'Node', 'help': 'Name of the node'},
                'age': {'title': 'Age', 'type': 'int', 'default': '18', 'range': [18, 100], 'help': 'age of the node'},
            },
            'Misc': {
                'nickname': {'title': 'Nickname', 'type': 'str', 'default': 'Node', 'help': 'Name of the node'},
                'gender': {'title': 'Gender', 'type': 'option', 'default': 'Unknown', 'range': ['Male', 'Female', 'Unknown'], 'help': 'Tags for the node'},
            }
        }


class Settings(ui.SettingsModelBase):
    def __init__(self, path):
        super().__init__(path)
        data_folder = osp.dirname(self.path)
        data_file = osp.join(data_folder, 'model.json')
        self.data = {
            'title': {'name': 'title', 'title': 'Window Title', 'type': 'str', 'default': 'My Demo App', 'value': 'My Demo App', 'help': 'Title of the app', 'tags': [], 'group': 'General'},
            'export': {'name': 'export', 'title': 'Export Data To File', 'type': 'file', 'default': data_file, 'value': data_file, 'range': [('JSON file', '*.json')], 'startDir': osp.dirname(data_file), 'help': 'Export model data to a file',
                       'tags': [],
                       'group': 'General'},
        }


class DemoTreeController(ui.TreeControllerBase):
    """
    Controller for the TreePane.
    """
    def __init__(self, model, settings):
        super().__init__(model, settings)

    def get_command_map(self):
        return {
            'Show Name': self.on_show_name,
            'Show Tags': self.on_show_tags,
        }

    def on_show_name(self):
        print('show name')

    def on_show_tags(self):
        print('show tags')

    def on_help(self):
        print('help')


class DemoApp:
    """
    Main application class.
    """
    def __init__(self):
        # Create the main window
        self.root = ui.Root("Demo App", (800, 600))
        self.treeModel = DemoTreeModel()
        export_to = osp.abspath(f'{util.get_platform_appdata_dir()}/my_demo_app/settings.json')
        self.settings = Settings(export_to)
        self.controller = DemoTreeController(self.treeModel, self.settings)

        # Create the TreePane
        self.treePane = ui.TreePane(self.root, "Tree", self.controller)
        self.treePane.pack(side="left", fill="both", expand=False)
        self.controller.bind_picker(self.treePane)

        # Create the PropertyPane
        self.propertyPane = ui.PropertyPane(self.root, self.controller)
        self.propertyPane.pack(side="right", fill="both", expand=True)
        self.controller.add_listener('prop', self.propertyPane)

        # Initialize the tree with data
        self.controller.fill()

        # Bind events
        self.root.mainloop()

if __name__ == "__main__":
    app = DemoApp()