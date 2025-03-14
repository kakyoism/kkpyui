import os.path as osp
import tkinter as tk
from tkinter import ttk
import sys
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/..'))
import kkpyui as ui


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
        return self.data[key]['children']

    def dump(self):
        """
        Dump the model into a group-prop pairs format for the PropertyPane.
        """
        return {
            'General': {
                'name': {'title': 'Name', 'type': 'str', 'default': 'Node', 'help': 'Name of the node'},
                'tags': {'title': 'Tags', 'type': 'str', 'default': '', 'help': 'Tags for the node'},
            }
        }

    def remove(self, keys):
        for key in keys:
            if key in self.data:
                del self.data[key]


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

    def on_mouse_ldown(self, event):
        super().on_mouse_ldown(event)
        selected = self.view.get_selection()
        if selected:
            self.update_properties(selected[0])

    def update_properties(self, node_key):
        """
        Update the property fields based on the selected node.
        """
        node = self.model.get(node_key)
        # if node:
        #     self.form.reset_entries()
        #     self.form.pages['General'].winfo_children()[0].set_data(node['name'])
        #     self.form.pages['General'].winfo_children()[1].set_data(node['tags'])
        print(node)


class DemoApp:
    """
    Main application class.
    """
    def __init__(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Demo App")
        self.root.geometry("800x600")
        self.tree_model = DemoTreeModel()
        self.settings = ui.Settings(osp.join(osp.dirname(__file__), 'settings.json'))
        self.tree_controller = DemoTreeController(self.tree_model, self.settings)

        # Create the TreePane
        self.tree_pane = ui.TreePane(self.root, "Tree", self.tree_controller)
        self.tree_pane.pack(side="left", fill="both", expand=True)

        # Create the PropertyPane
        self.property_pane = ui.PropertyPane(self.root, self.tree_controller)
        self.property_pane.pack(side="right", fill="both", expand=True)

        # Initialize the tree with data
        self.tree_controller.fill()

        # Bind events
        self.root.mainloop()

if __name__ == "__main__":
    app = DemoApp()