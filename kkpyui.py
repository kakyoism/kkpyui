import csv
import json
import os.path as osp
import queue
import threading
import time
import tkinter as tk
import traceback
import types
import typing
from tkinter import ttk, filedialog, scrolledtext as tktext, simpledialog as tkdialog
from tkinter import messagebox as tkmsgbox
from tkinter.font import Font as tkFont
# 3rd party
import kkpyutil as util


class ProgressEvent(threading.Event):
    def __init__(self):
        super().__init__()
        self.topic = None
        self.progress = -1
        self.description = None

    def set_progress(self, topic, progress, description):
        self.topic = topic
        self.progress = progress
        self.description = description
        self.set()


class ErrorEvent(threading.Event):
    def __init__(self):
        super().__init__()
        self.error = None
        self.callstack = None

    def __repr__(self):
        return f'Error: {self.error}'

    def set_error(self, error: Exception, callstack: str):
        """
        - callstack: traceback.format_exc()
        """
        self.error = error
        self.error.callstack = callstack
        self.set()


class Globals:
    root = None
    progEvent = ProgressEvent()
    abortEvent = threading.Event()
    errorEvent = ErrorEvent()
    style = None


def init_style():
    Globals.style = ttk.Style()
    Globals.style.theme_use('clam')
    # fonts
    node_font = tkFont(family="Helvetica", size=10, weight="bold")
    # frames
    Globals.style.configure('TFrame', background='#303841', foreground='white', borderwidth=5)
    # form
    Globals.style.configure('Page.TLabelframe', background="#303841", foreground="#DDD", relief="flat", borderwidth=2, font=node_font)
    Globals.style.configure('Page.TLabelframe.Label', background="#303841", foreground="#DDD")
    # action bar
    Globals.style.configure('ActionBar.TFrame', background='#2e3238', foreground='white', borderwidth=0)
    # progress bar
    Globals.style.configure("Horizontal.TProgressbar",
                            troughcolor='#2e3238',  # Dark background
                            background='#5bc0de',  # Greenish progress bar
                            bordercolor='#1c1d1f',
                            lightcolor='#2e3238',
                            darkcolor='#2e3238')
    Globals.style.layout("Horizontal.TProgressbar",
                         [('Horizontal.Progressbar.trough',
                           {'children': [('Horizontal.Progressbar.pbar',
                                          {'side': 'left', 'sticky': 'ns'})],
                            'sticky': 'nswe'})])
    # tree view
    Globals.style.configure("NavBar.Treeview",
                            background="#22262a",
                            foreground="#DDD",
                            fieldbackground="#22262a",
                            borderwidth=0,
                            relief="flat")
    # Treeview heading style (for column headers)
    Globals.style.configure("NavBar.Treeview.Heading",
                            background="#555",
                            foreground="#CCC",
                            relief="flat")
    # Change selected color
    Globals.style.map("NavBar.Treeview",
                      background=[('selected', '#27547d')])
    #
    # interactive form widgets
    #
    Globals.style.configure('TButton', background='#5a505d', foreground='white', borderwidth=0)
    Globals.style.map("TButton",
                      background=[("active", "#777")])
    Globals.style.configure('TLabel', background='#303841', foreground='white', borderwidth=1)
    # primary button
    Globals.style.configure('Primary.TButton', background='#3f597c', foreground='white', borderwidth=2)
    # scrollbar
    Globals.style.configure("Vertical.TScrollbar", troughcolor="#222")
    Globals.style.map("Vertical.TScrollbar",
                      grip=[('!disabled', '#404040'), ('active', '#505050'), ('disabled', '#2d2d2d')],
                      background=[('!disabled', '#404040'), ('active', '#505050'), ('disabled', '#2d2d2d')])
    # combobox
    Globals.style.configure("TCombobox", foreground="#DDD", background="#333",
                            fieldbackground="#555", selectbackground="#666",
                            selectforeground="#DDD", arrowcolor="white")
    Globals.style.map('TCombobox', fieldbackground=[('readonly', '#333')])
    # spinbox
    Globals.style.configure("TSpinbox",
                            fieldbackground="#2E2E2E",  # Dark color for the field background
                            foreground="#DDD",  # Light color for the text
                            background="#333",  # Dark color for the Spinbox background (buttons area)
                            bordercolor="#333",
                            borderwidth=0,
                            arrowsize=10)

    Globals.style.map("TSpinbox",
                      fieldbackground=[("active", "#333333"), ("disabled", "#1E1E1E")],
                      foreground=[("active", "#FFF"), ("disabled", "#888")],
                      background=[("readonly", "#2E2E2E")],
                      arrowcolor=[("active", "#DDD"), ("disabled", "#888")])
    # slider
    Globals.style.configure("Horizontal.TScale",
                            background="#2E2E2E",  # Dark grey, same as the Spinbox
                            troughcolor="#555555",  # A slightly lighter grey for the trough
                            bordercolor="#404040",  # A subtle border for the trough
                            sliderrelief="flat",
                            sliderlength=20)

    Globals.style.map("Horizontal.TScale",
                      slider=[("active", "#555555"), ("disabled", "#2E2E2E")],  # Slider styles
                      background=[("active", "#404040"), ("disabled", "#333333")])  # Background styles when active or disabled
    # checkbox
    Globals.style.configure("TCheckbutton",
                            background="#303841",  # Dark grey background
                            foreground="#DDD",  # Light grey text color for readability
                            selectcolor="#555",  # Darker background for the checkbox itself
                            bordercolor="#555",
                            relief="flat")

    Globals.style.map("TCheckbutton",
                      background=[('active', '#333'), ('selected', '#303841')],  # Darker background when active, blue when selected
                      foreground=[('disabled', '#888')],  # Greyed out text when disabled
                      indicatorbackground=[('selected', '#1E6FBA'), ('!selected', '#555')],  # Blue check mark when selected
                      indicatorforeground=[('selected', '#DDD')])  # Dark grey check mark when not selected
    Globals.style.configure("TEntry",
                            foreground="white",  # Light grey for text
                            background="#555",  # Dark grey for the entry background
                            insertbackground="#DDD",  # Light grey for the cursor color
                            fieldbackground="#333333",  # Dark grey for the field background
                            borderwidth=0,
                            relief="flat")
    # menubutton, optinonmenu
    Globals.style.configure("TMenubutton", background="#333", foreground="#DDD", arrowcolor="white")
    # Configure the OptionMenu dropdown (menu) colors
    Globals.style.configure("TMenu", background="#333", foreground="#DDD", activebackground='#444', activeforeground='#FFF')
    Globals.style.map("TMenubutton",
              background=[("active", "#4D4D4D")],  # Darker shade for hover
              foreground=[("active", "#FFF")],  # Optional: change text color on hover
              arrowcolor=[("active", "#FFF")])  # Change arrow color on hover


def safe_get_number(tknumvar: tk.Variable):
    """
    - swallow crash and give caller clues to handle with
    - when it's not a number, the caller should not use the value and choose one of the following strategies:
      - early out silently
      - reset to default value
      - throw exception
    """
    try:
        return tknumvar.get()
    except tk.TclError as e:
        util.glogger.warning(f'Value error: {e}')
        # get uesr input from exception message
        # - e.g., 'expected integer but got "abc"'
        user_input = str(e).split(' ')[-1].removeprefix('"').removesuffix('"')
        return user_input


class Root(tk.Tk):
    def __init__(self, title, size=(800, 600), icon=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        screen_size = (self.winfo_screenwidth(), self.winfo_screenheight())
        self.geometry('{}x{}+{}+{}'.format(
            size[0],
            size[1],
            int(screen_size[0] / 2 - size[0] / 2),
            int(screen_size[1] / 2 - size[1] / 2))
        )
        # self.validateIntCmd = (self.register(_validate_int), '%P', '%S', '%W')
        # self.validateFloatCmd = (self.register(_validate_float), '%P', '%S', '%W')
        if icon:
            self.iconphoto(True, tk.PhotoImage(file=icon))
        self.controller = None
        # used by on_during_deactivate only for the shutdown sequence only
        self.isActive = False
        self._auto_focus()

    def set_controller(self, controller):
        """
        - controller is used in many non-contiguous calls in the init sequence
        - so for DRY, it needs to be a member
        - it's created after root because views that it knows must use root as their parent,
        - so we set it using a setter whenever there is a chance
        """
        self.controller = controller

    def bind_events(self):
        """
        - controller interface must implement:
          - ENTER key event: default action
          - ESC key event: cancel/negate default action
          - Window X button event: quit
        - refer to Inter-Client Communication Conventions Manual ICCCM for possible window events
        """
        self.bind("<Return>", self.controller.on_submit)
        self.bind("<Escape>", lambda event: self.controller.on_cancel(event))
        # Expose: called even when slider is dragged, so we don't use it
        # Map: triggered when windows are visible, called every frame
        # Destroy: triggered when windows are closed, called every frame
        self.bind('<Map>', lambda event: self.on_during_activate(event))
        self.bind('<Destroy>', lambda event: self.on_during_deactivate(event))
        # startup event: init(), must be called by client
        # bind X button to quit the program
        self.protocol('WM_DELETE_WINDOW', self.controller.on_quit)

    def _auto_focus(self):
        def _unpin_root(event):
            """
            - root may be hidden behind other apps on first run
            - so we pin it to top first then unpin it
            """
            if isinstance(event.widget, tk.Tk):
                event.widget.attributes('-topmost', False)

        self.attributes('-topmost', True)
        self.focus_force()
        self.bind('<FocusIn>', _unpin_root)

    def mainloop(self, n: int = 0):
        """
        - prepend custom pre-startup event
        - this solves the problem where <Map> event, being a per-frame activation event, gets called many times instead of just once, which is redundant for startup logic
        """
        self.controller.update_model()
        self.after(0, self.controller.on_startup)
        super().mainloop()

    def on_during_activate(self, event):
        """
        - called every frame during the root window display process, i.e., from background to foreground
        - but since app-level startup tasks only need to be done once, we bootstrap the frame-behavior for controller to perform app-level tasks
        """
        if self.isActive:
            return
        self.controller.on_activate(event)
        self.isActive = True

    def on_during_deactivate(self, event):
        """
        - similar to on_during_activate(), but for shutdown
        """
        if not self.isActive:
            return
        self.controller.on_deactivate(event)
        self.isActive = False


class Prompt:
    """
    - must use within tkinter mainloop
    - otherwise the app will freeze upon confirmation
    """

    def __init__(self, master=Globals.root, logger=None):
        self.master = master
        self.logger = logger or util.glogger

    def info(self, msg, confirm=True):
        """Prompt with info."""
        self.logger.info(msg)
        if confirm:
            tkmsgbox.showinfo('Info', msg, icon='info', parent=self.master)

    def warning(self, detail, advice, question='Continue?', confirm=True):
        """
        - for problems with minimum or no consequences
        - user can still abort, but usually no special handling is needed
        """
        msg = f"""\
Detail:
{detail}

Advice:
{advice}

{question if confirm else 'Will continue anyways'}"""
        self.logger.warning(msg)
        if not confirm:
            return True
        return tkmsgbox.askyesno('Warning', msg, icon='warning', parent=self.master)

    def error(self, errclass, detail, advice, confirm=True):
        """
        - for problems with significant impact
        - the program will crash immediately if not to confirm
        """
        msg = f"""\
Detail:
{detail}

Advice:
{advice}

Will crash"""
        self.logger.error(msg)
        if confirm:
            tkmsgbox.showerror('Error', msg, icon='error', parent=self.master)
        raise errclass(msg)


class Page(ttk.LabelFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, text=title, **kwargs)
        self.grid_columnconfigure(0, weight=1)

    @staticmethod
    def add(entries):
        """
        - vertical layout
        """
        for entry in entries:
            entry.layout()

    def get_title(self):
        return self.cget('text')

    def layout(self):
        self.pack(fill="x", pady=5)
        self.configure(style='Page.TLabelframe')


class ScrollFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        def _configure_interior(event):
            """
            - without this, scrollbar will not be configured properly
            - because the inner frame initially does not fill the canvas
            """
            # Update the scrollbars to match the size of the inner frame.
            width, height = (self.frame.winfo_reqwidth(),
                             self.frame.winfo_reqheight())
            self.canvas.configure(scrollregion=(0, 0, width, height), bg='#303841', highlightthickness=0)
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.frame.winfo_reqwidth())

        def _configure_canvas(event):
            # update the inner frame's width to fill the canvas
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.itemconfigure(frame_id, width=self.canvas.winfo_width())

        super().__init__(master, *args, **kwargs)
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style='Vertical.TScrollbar')
        # scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.frame = ttk.Frame(self.canvas,)
        frame_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.frame.bind('<Configure>', _configure_interior)
        self.canvas.bind('<Configure>', _configure_canvas)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame.bind("<Enter>", self._bound_to_mousewheel)
        self.frame.bind("<Leave>", self._unbound_to_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mouse_scroll(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_scroll)

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")


class Form(ttk.PanedWindow):
    """
    - accepts and creates navbar for input pages
    - layout: page-based navigation
    - filter: locate form entries by searching for title keywords
    - structure: Form > Page > Entry
    - instantiation: Form > Page (slaved to form pane) > Entry (slaved to page)
    """

    def __init__(self, master, page_titles: list[str], **kwargs):
        super().__init__(master, orient=tk.HORIZONTAL)
        # Left panel: navigation bar with filtering support
        self.navPane = ttk.Frame(self, width=200,)
        self.navPane.pack_propagate(False)  # Prevent the widget from resizing to its contents
        # Create a new frame for the search box and treeview
        search_box = ttk.Frame(self.navPane)
        search_box.pack(side="top", fill="x")
        self.searchEntry = ttk.Entry(search_box)
        self.searchEntry.pack(side="left", fill="x", expand=True)
        self.searchEntry.bind("<KeyRelease>", self.filter_entries)
        self.searchEntry.bind("<Control-BackSpace>", self._on_clear_search)
        # Place the treeview below the search box
        self.tree = ttk.Treeview(self.navPane, show="tree", style='NavBar.Treeview')
        self.tree.heading("#0", text="", anchor="w")  # Hide the column header
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.update_entries)
        # Right panel: entries in page
        self.entryPane = ScrollFrame(self,)
        # build form with navbar and page frame
        self.add(self.navPane, weight=0)
        self.add(self.entryPane, weight=1)
        self.pages = {title.lower(): Page(self.entryPane.frame, title.title(),) for title in page_titles}
        self.prompt = Prompt()
        self.init()
        self.layout()

    def layout(self):
        self.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.configure(style='TFrame')
        node_font = tkFont(family="Helvetica", size=10, weight="bold")
        self.tree.tag_configure('boldtext', font=node_font)

    def init(self):
        # Populate tree with page titles
        for title, pg in self.pages.items():
            self.tree.insert("", "end", text=title.title())
        # select first page
        self.tree.selection_set(self.tree.get_children()[0])
        self.update_entries(None)

    def update_entries(self, event):
        """
        - the first call is triggered at binding time? where nothing is selected yet
        - app must always create a group
        """
        selected_item = self.tree.focus()
        # selection will be blank on startup because no item is selected
        selected_title = self.tree.item(selected_item, "text")
        # Hide all pages
        for pg in self.pages.values():
            pg.pack_forget()
        # After hiding, update the right pane to ensure correct display
        self.pages[selected_title.lower()].layout() if selected_title else list(self.pages.values())[0].layout()
        self.entryPane.update()

    def _on_clear_search(self, event):
        if event.state != 4 or event.keysym != 'BackSpace':
            return
        self.searchEntry.delete(0, tk.END)
        self.filter_entries(None)

    def filter_entries(self, event):
        """
        - must preserve entry order when keyword is cleared
        TODO: optimize rebuilding speed
        """
        keyword = self.searchEntry.get().strip().lower()
        if not keyword:
            for title, pg in self.pages.items():
                for entry in pg.winfo_children():
                    entry.pack_forget()
            # After hiding, update the right pane to reset the initial display
            for title, pg in self.pages.items():
                for entry in pg.winfo_children():
                    entry.layout()
            self.entryPane.update()
            return
        for title, pg in self.pages.items():
            for entry in pg.winfo_children():
                assert isinstance(entry, Entry)
                if keyword not in entry.text.lower():
                    entry.pack_forget()
                    continue
                entry.layout()
        self.entryPane.update()

    def validate_entries(self):
        for title, pg in self.pages.items():
            for entry in pg.winfo_children():
                if not entry.validate_data():
                    return False
        return True

    def reset_entries(self):
        for title, pg in self.pages.items():
            for entry in pg.winfo_children():
                entry.reset()


class Entry(ttk.Frame):
    """
    - used as user input, similar to CLI arguments
    - widget must belong to a group
    - groups form a tree to avoid overloading parameter panes
    - groups also improve SNR by prioritizing frequently-tweaked parameters
    - page is responsible for lay out entries
    """

    def __init__(self, master: Page, key, text, widget_constructor, default, doc, presetable=True, **widget_kwargs):
        super().__init__(master,)
        assert isinstance(self.master, Page)
        self.master.add([self])
        self.key = key
        self.text = text
        self.default = default
        self.isPresetable = presetable
        # model-binding
        self.data = None
        # title
        self.label = ttk.Label(self, text=self.text, cursor='hand2', style='TLabel')
        self.label.pack(side='top', expand=True, padx=5, pady=2, anchor="w")
        self.label.bind("<Double-Button-1>", lambda e: tkmsgbox.showinfo("Help", doc))
        # field
        self.field = widget_constructor(self, **widget_kwargs)
        self.columnconfigure(0, weight=1)
        self.field.pack(expand=True, padx=5, pady=2, anchor="w")
        # context menu
        self.contextMenu = tk.Menu(self, tearoff=0, bg='#333', fg='#DDD', bd=1, relief='flat', activebackground='#444', activeforeground='#FFF')
        # use a context menu instead of direct clicking to avoid accidental reset
        self.contextMenu.add_command(label="Help", command=lambda: tkmsgbox.showinfo("Help", doc))
        self.contextMenu.add_command(label="Reset", command=self.reset)
        # maximize context-menu hitbox
        # - macos
        self.field.bind("<Button-2>", self.show_context_menu)
        # - windows
        self.label.bind("<Button-3>", self.show_context_menu)
        # getting out of focus so that key strokes will not be intercepted by the entry
        self.field.bind("<Escape>", lambda event: Globals.root.focus_set())

    def _init_data(self, var_cls):
        return var_cls(master=self, name=self.text, value=self.default)

    def reset(self):
        self.set_data(self.default)

    def get_data(self):
        return self.data.get()

    def set_data(self, value):
        self.data.set(value)

    def layout(self):
        self.pack(fill="both", expand=True, padx=5, pady=10, anchor="w")

    def show_context_menu(self, event):
        try:
            self.contextMenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.contextMenu.grab_release()

    def set_tracer(self, handler):
        """
        - handler: callback (name, var, index, mode)
          - name: name of the variable
          - var: tk.Variable object
          - index: index of the variable
          - mode: 'read' (triggered when var is read), 'write'(triggered when var is written), 'unset'
        """
        self.data.trace_add('write', callback=lambda name, index, mode, var=self.data: handler(name, var, index, mode))

    def validate_data(self):
        print(f'{self.__class__}: subclass data validation: call this when out of focus and submitting the form')
        return True


class FormMenu(tk.Menu):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        assert isinstance(self.master, tk.Tk)
        self.master.configure(menu=self)
        self.controller = controller
        self.fileMenu = tk.Menu(self, tearoff=False, bg='#333', fg='#DDD', bd=1, relief='flat', activebackground='#444', activeforeground='#FFF')
        self.fileMenu.add_command(label="Load Preset ...", command=self.on_load_preset)
        self.fileMenu.add_command(label="Save Preset ...", command=self.on_save_preset)
        self.fileMenu.add_command(label="Quit", command=self.on_quit, accelerator="Ctrl+Q")
        self.master.bind("<Control-q>", lambda event: self.on_quit())
        self.master.bind("<Control-Q>", lambda event: self.on_quit())
        self.helpMenu = tk.Menu(self, tearoff=False, bg='#333', fg='#DDD', bd=1, relief='flat', activebackground='#444', activeforeground='#FFF')
        self.helpMenu.add_command(label="Open User Guide", command=self.on_open_help, accelerator="F1")
        self.helpMenu.add_command(label="Open Diagnostics", command=self.on_open_diagnostics)
        self.helpMenu.add_command(label="Report A Problem", command=self.on_report_issue)
        self.master.bind("<F1>", lambda event: self.on_open_help())
        self.add_cascade(label="File", menu=self.fileMenu)
        self.add_cascade(label="Help", menu=self.helpMenu)

    def on_load_preset(self):
        preset = filedialog.askopenfilename(title="Load Preset", filetypes=[
            # tkinter openfile dialog filter does not accept middlename,
            # so *.preset.json won't work here
            ("Preset Files", "*.json"),
        ])
        if preset:
            self.controller.load_preset(preset)

    def on_save_preset(self):
        preset = filedialog.asksaveasfilename(title="Save Preset", filetypes=[
            ("Preset Files", "*.preset.json"),
        ])
        if preset:
            self.controller.save_preset(preset)

    def on_open_help(self):
        self.controller.on_open_help()

    def on_open_diagnostics(self):
        self.controller.on_open_diagnostics()

    def on_report_issue(self):
        self.controller.on_report_issue()

    def on_quit(self):
        self.controller.on_quit(None)


class FormController:
    """
    - observe all entries and update model
    - both form and realtime apps can use this class
    - form apps can use submit() to update model
    - realtime apps can set arg-tracers
    - model and app-config share the same keys
    - backend task works in task thread
    - progressbar and task synchronize via threading.Event
    """

    def __init__(self, form=None, model=None, to_block=True):
        self.form = form
        self.model = model
        self.taskThread = None
        self.progUI = None
        self.progEvent = Globals.progEvent
        self.abortEvent = Globals.abortEvent
        self.toBlockWhileAwait = to_block

    def validate_form(self):
        return self.form.validate_entries()

    def update_model(self):
        config_by_page = {
            pg.get_title(): {entry.key: entry.get_data() for entry in pg.winfo_children()}
            for title, pg in self.form.pages.items()
        }
        self.model = {k: v for entries in config_by_page.values() for k, v in entries.items()}

    def update_view(self):
        self.load_preset(self.model)

    def load_preset(self, preset):
        """
        - model includes input and config
        - input is runtime data that changes with each run
        - only config will be saved/loaded as preset
        """
        config = util.load_json(preset) if isinstance(preset, str) else preset
        for title, page in self.form.pages.items():
            for entry in page.winfo_children():
                try:
                    entry.set_data(config[entry.key])
                except KeyError as e:
                    util.glogger.error(f'{entry.key=}, {entry.data.get()=}, {self.model=}: {e}')
                except Exception as e:
                    util.glogger.error(f'{entry.key=}, {entry.data.get()=}, {self.model=}: {e}')

    def save_preset(self, preset):
        """
        - only config is saved
        - input always belongs to group "input"
        - in app-config, if user specifies title, then the title is used with presets (titlecase) instead of the original key (lowercase)
        """
        config_by_page = {
            pg.get_title(): {entry.key: entry.get_data() for entry in pg.winfo_children() if entry.isPresetable}
            for title, pg in self.form.pages.items()
        }
        config = {k: v for entries in config_by_page.values() for k, v in entries.items()}
        util.save_json(preset, config)

    def is_scheduled_to_stop(self):
        return self.abortEvent.is_set()

    def bind_progress(self, prog_ui):
        self.progUI = prog_ui

    def start_progress(self):
        """
        - only used by indeterminate progressbar
        """
        self.send_progress('Progress', 0, 'Starting ...')

    def stop_progress(self):
        """
        - only used by indeterminate progressbar
        """
        self.send_progress('Progress', 100, 'Starting ...')

    def send_progress(self, topic, progress, description):
        """
        - called by the task thread
        """
        self.progEvent.set_progress(topic, progress, description)

    def get_latest_model(self):
        """
        - for easy consumption of client objects as arg
        """
        self.update_model()
        return types.SimpleNamespace(**self.model)

    def await_task(self, wait_ms=100):
        self.progUI.poll(wait_ms)
        if self.toBlockWhileAwait:
            self.taskThread.join()
            self.on_task_done()

    #
    # callbacks
    #
    def on_open_help(self):
        """
        - open help doc, e.g., webpage, local file
        - subclass this for your own 
        """
        self.info('Help not implemented yet; implement it in controller subclasses', confirm=True)

    def on_open_diagnostics(self):
        """
        - open log or app session data is hard to generalize
        - subclass this to use app-level logging scheme
        - e.g., opening a log file using the default browser
        - e.g., opening a folder containing the entire diagnostics
        """
        self.info('Logging not implemented yet; implement it in controller subclasses', confirm=True)

    def on_report_issue(self):
        """
        - report bug to the developer
        - subclass this
        """
        self.info('Bug reporting not implemented yet; implement it in controller subclasses', confirm=True)

    def on_reset(self):
        """
        - reset all form fields to default
        - usually can be used as is, no need to override
        """
        self.form.reset_entries()

    def on_submit(self, event=None):
        """
        - main action to launch the background task
        - usually can be used as is, no need to override
        """
        if self.taskThread and self.taskThread.is_alive():
            return
        if not self.validate_form():
            return
        self.update_model()
        self.abortEvent.clear()
        if self.progUI:
            self.progUI.init()
        # lambda wrapper ensures "self" is captured by threading as a context
        # otherwise ui thread still blocks
        self.taskThread = threading.Thread(target=self.run_task, daemon=True)
        self.taskThread.start()
        self.await_task(33)

    def run_task(self):
        """
        - override this in app
        - run actual task synchronously, no need to spawn thread
        """
        raise NotImplementedError('subclass this!')

    def on_task_done(self):
        """
        - app-land callback (ui thread) called when task is done
        - must override this in app
        """
        raise NotImplementedError('subclass this!')

    def on_cancel(self, event=None):
        """
        - cancelling a running background task
        """
        if self.taskThread and self.taskThread.is_alive():
            self.abortEvent.set()

    def on_quit(self, event=None):
        """
        CAUTION:
        - usually we avoid direct view-ops in controller
        - but here it is necessary for sharing binding between menu, x-button, and other quitting devi
        """
        if not self.on_shutdown():
            # user cancelled
            return
        self.form.master.quit()

    def on_startup(self):
        """
        - called just before showing root window (<Map>, on_activate()), after all fields are initialized
        - so that fields can be used here for the first time
        """
        pass

    def on_shutdown(self) -> bool:
        """
        - called just before quitting
        - safely schedules shutdown with prompt and early-outs if user cancels
        - subclass this for post-ops
        """
        if not self.taskThread or not self.taskThread.is_alive():
            # task not running, safe to continue to quit
            self.abortEvent.set()  # progressbar needs to be stopped
            return True
        prompt = Prompt()
        # Make default behavior a safe bet
        if prompt.warning('Quitting a running task may cause damage. Click Yes to wait for it to finish, or No to force-quit', 'Wait for it to finish.', question='Keep waiting?', confirm=True):
            # user decided to wait
            return False
        self.abortEvent.set()  # progressbar needs to be stopped
        # task should have received stop event, let's wait for it to end
        # it may choose a safe-quit path, but maybe not (damage)
        return True

    def on_activate(self, event=None):
        """
        - binding of <Map> event as logical initialization
        - called once when the root window displays, i.e., from background to foregrounded
        """
        pass

    def on_deactivate(self, event=None):
        """
        - binding of <Destroy> event as logical termination
        - called AFTER triggering WM_DELETE_WINDOW
        - called once when the root window disappears, from foreground to background
        - on macOS: called on Cmd+Q key-combo, which quits python launcher and bypasses WM_DELETE_WINDOW
        """
        if util.PLATFORM == 'Darwin':
            self.on_quit()

    def info(self, msg, confirm=True):
        self.form.prompt.info(msg, confirm)

    def warning(self, detail, advice, question='Continue?', confirm=True):
        return self.form.prompt.warning(detail, advice, question, confirm)

    def error(self, errclass, detail, advice, confirm=True):
        return self.form.prompt.error(errclass, detail, advice, confirm)


class FormActionBar(ttk.Frame):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # action logic
        self.controller = controller
        # occupy the entire width
        # new buttons will be added to the right
        self.resetBtn = ttk.Button(self, text="Reset", command=self.on_reset)
        self.separator = ttk.Separator(self, orient="horizontal")
        # Create Cancel and Submit buttons
        self.cancelBtn = ttk.Button(self, text="Stop", command=self.on_cancel)
        self.submitBtn = ttk.Button(self, text="Start", command=self.on_submit, cursor='hand2', style='Primary.TButton')
        # layout: keep the order
        self.separator.pack(fill="x")
        # left-most must pack after separator to avoid occluding the border
        self.resetBtn.pack(side="left", padx=10, pady=5)
        self.submitBtn.pack(side="right", padx=10, pady=10)
        self.cancelBtn.pack(side="right", padx=10, pady=10)
        self.layout()

    def layout(self):
        self.pack(side="bottom", fill="x")
        self.configure(style='ActionBar.TFrame')

    def on_reset(self, event=None):
        self.controller.on_reset()

    def on_cancel(self, event=None):
        self.controller.on_cancel()

    def on_submit(self, event=None):
        self.controller.on_submit()


class WaitBar(ttk.Frame):
    """
    - app must run in worker thread to avoid blocking UI
    - use /start, /stop, /processing to mark start/end/progress
    - when using subprocess to run a blackbox task, use indeterminate mode cuz there is no way to pass progress back
    - protocol: tuple(stage, progress, description), where stage is program instruction, description is for display
    - TODO: use IPC for cross-language open-source tasks
    """

    def __init__(self, master, producer, prog_evt=None, abort_evt=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.desc = tk.StringVar(name='description', value='')
        self.bar = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.label = ttk.Label(self.bar, textvariable=self.desc, text='...', foreground='white', background='black')
        self.topic = None
        self.progEvent = prog_evt or Globals.progEvent
        self.abortEvent = abort_evt or Globals.abortEvent  # read-only here, set by app
        self.bind(producer)
        self.layout()

    def layout(self):
        """
        - overlay label on top of bar
        """
        self.bar.pack(side="right", fill="x", expand=True)
        self.label.place(relx=0.5, rely=0.5, anchor='center')
        self.pack(side='bottom', fill='both', expand=False)

    def bind(self, producer):
        producer.bind_progress(self)

    def init(self):
        self.progEvent.clear()
        self.abortEvent.clear()

    def _scheduled_to_stop(self):
        return self.abortEvent.is_set()

    def start(self, topic: str, description: str = None):
        """
        - called by app's task thread
        """
        self.topic = topic
        if description:
            self.desc = description
        self.bar.start()

    def stop(self, description: str = None):
        """
        - called by app's task thread
        """
        # self.send_progress(self.topic, 100, description)
        if description:
            self.desc = description
        self.bar.stop()

    def send_progress(self, topic: str, progress: int, description: str = None):
        """
        - call this in app's controller.run_task() (task thread) to send progress to ui thread
        """
        self.progEvent.set_progress(topic, progress, description)

    def receive_progress(self, topic: str, progress: int, description: str = '...'):
        """
        - call this in .poll() (ui thread) to receive progress from task thread
        """
        self.topic = topic
        if progress == 0:
            self.bar.start()
        elif progress >= 100:
            self.bar.stop()
            self.abortEvent.set()
        self.desc.set(description)
        self.update_idletasks()
        self.progEvent.clear()

    def poll(self, wait_ms=100):
        """
        - for modal progressbar only
        - do not use this for non-blocking scenarios such as music player's control panel
        """

        if not self._scheduled_to_stop() and self.progEvent.is_set():
            self.receive_progress(self.progEvent.topic, self.progEvent.progress, self.progEvent.description)
        if self._scheduled_to_stop():
            self.stop()
            return
        self.master.after(wait_ms, self.poll)


class ProgressBar(WaitBar):
    def __init__(self, master, producer, *args, **kwargs):
        super().__init__(master, producer, *args, **kwargs)
        self.prog = tk.IntVar(name='progress', value=0)
        self.bar.configure(variable=self.prog, mode='determinate')
        self.layout()

    def init(self):
        super().init()
        self.prog.set(0)
        self.master.update_idletasks()

    def receive_progress(self, topic: str, progress: int, description: str = '...'):
        # print(f'receiving progress ... {topic=}, {progress=}, {description=}')
        self.prog.set(progress)
        self.desc.set(description)
        self.update_idletasks()
        self.progEvent.clear()
        if progress >= 100:
            self.abortEvent.set()


class ProgressPrompt:
    """
    - popup progress dialog.
    - support determinate and indeterminate progress
    - using threading events to synchronize progress between ui and task threads
    - sync must have attributes:
      - progEvent (ui.ProgressEvent)
      - abortEvent (threading.Event)
      - errorEvent (ui.ErrorEvent)
    - help must have attributes:
      - reporter (callable)
      - cookie (any object), optional argument for reporter function
      - helper (dict: {exception: url})
    """
    def __init__(self, master, determinate=True, sync=None, help=None):
        # data
        self.master = master
        self.isDeterminate = determinate
        self.topicVar = tk.StringVar(name='progress', value='Progress')
        self.progVar = tk.IntVar(name='progress', value=0)
        self.descVar = tk.StringVar(name='description', value='')
        if not sync:
            sync = Globals
        self.progEvent = sync.progEvent
        self.abortEvent = sync.abortEvent
        self.errorEvent = sync.errorEvent
        self.reporter = help.reporter if help else None
        self.cookie = help.cookie if help else None
        self.helper = help.helper if help else {}
        # ui
        self.window = None
        self.labelFrame = None
        self.descLabel = None
        self.progLabel = None
        self.progBar = None

    def _create_window(self, title):
        """Dynamically creates the progress bar window."""
        def _center_over_parent():
            """
            - place the modal dialog in the center of the parent window
            """
            parent = self.window.master
            parent.update_idletasks()
            parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
            parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
            dialog_width, dialog_height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
            x, y = parent_x + (parent_width // 2) - (dialog_width // 2), parent_y + (parent_height // 2) - (dialog_height // 2)
            self.window.geometry(f"+{x-100}+{y-100}")
        self.window = tk.Toplevel(self.master)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        self.window.transient(self.master)
        self.window.grab_set()  # Make modal
        # Label frame for information and progress text
        self.labelFrame = ttk.Frame(self.window)
        self.labelFrame.pack(side='top', fill="x", padx=10, pady=5, expand=True)
        self.labelFrame.columnconfigure(0, weight=1)
        self.labelFrame.columnconfigure(1, weight=1)
        # Left label for general info
        self.descLabel = ttk.Label(self.labelFrame, textvariable=self.descVar, text="Running task ...", anchor="w")
        self.descLabel.pack(side='left', fill="x", padx=5, expand=True)
        # Right label for showing determinate progress
        if self.isDeterminate:
            perc_label = ttk.Label(self.labelFrame, text="%", anchor="e")
            perc_label.pack(side='right')
            self.progLabel = ttk.Label(self.labelFrame, textvariable=self.progVar, text="0", anchor="e")
            self.progLabel.pack(side='right', fill="x", padx=1)
        # Progress bar
        self.progBar = ttk.Progressbar(self.window, variable=self.progVar, mode="determinate" if self.isDeterminate else "indeterminate")
        self.progBar.pack(side='bottom', fill="x", padx=10, pady=5, expand=True)
        _center_over_parent()
        self.window.update_idletasks()
        self.window.protocol(x_button_event := "WM_DELETE_WINDOW", self.term)

    def init(self, task="Progress"):
        """
        - shows the modal progress prompt
        """
        self._clear_events()
        if not self.window:
            self._create_window(task)
        self.progVar.set(0)
        self.descVar.set(task)

    def term(self):
        """
        - clean up and closes the progress prompt
        """
        self.progVar.set(100);
        self.descVar.set("Stopping ...")
        self._clear_events()
        self.close()

    def _clear_events(self):
        self.progEvent.clear()
        self.errorEvent.clear()
        self.abortEvent.clear()

    def _scheduled_to_stop(self):
        return self.abortEvent.is_set() or not self.window

    def poll(self, wait_ms=100):
        if self.errorEvent.is_set():
            self.errorEvent.clear()
            error_prompt = ErrorPrompt(self.master, self.errorEvent.error, util.glogger)  # Replace `print` with your logger
            error_prompt.bind_reporter(self.reporter, self.cookie)
            error_prompt.bind_helper(self.helper)
            self.term()
            return
        if not self._scheduled_to_stop() and self.progEvent.is_set():
            self.receive_progress(self.progEvent.topic, self.progEvent.progress, self.progEvent.description)
            self.window.update_idletasks()
            self.progEvent.clear()
        if self._scheduled_to_stop():
            return
        self.window.after(wait_ms, self.poll)

    def send_progress(self, topic: str, progress: int, description: str = None):
        """
        - call this in task thread to send progress to ui thread
        """
        self.progEvent.set_progress(topic, progress, description)

    def receive_progress(self, topic: str, progress: int, description: str = '...'):
        """
        - poll this in ui thread to receive progress from task thread
        - client does not know the difference between determinate and indeterminate
        - client only knows the progress is 0-100, when the progress is unkonwn, simply send 0 to start, and 100 to stop
        """
        self.topicVar.set(topic)
        if not self.isDeterminate:
            if progress == 0:  # starting
                self.progBar.start()
            elif progress >= 100:  # stopping
                self.progBar.stop()
                self.abortEvent.set()
        else:
            self.progVar.set(progress)
            if progress >= 100:
                self.abortEvent.set()
        self.descVar.set(description)
        self.window.update_idletasks()
        self.progEvent.clear()

    def describe(self, message):
        """
        - mainly for indeterminate progress
        """
        self.descVar.set(message)

    def close(self):
        """
        - close window only
        - the prompt can be reused by calling init()
        """
        if self.window:
            self.window.destroy()
            self.window = None


class ErrorPrompt(tk.Toplevel):
    """
    - catch exceptions and give guidance, including user-defined and uncaught
    - show error messages with friendly pacing
    - provide a bug-report interface for app to plug in issue trackers
    - avoid user dismissing the error window prematurely
    """
    def __init__(self, parent, exception, logger):
        super().__init__(parent)
        self.exception = exception
        self.logger = logger
        self.reporter = None
        self.errHelpMap = None
        # ui
        self.title("Error")
        self.geometry("600x400")
        # Make the window modal
        self.transient(parent)
        self.grab_set()
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.traceText = tk.Text(frame, wrap=tk.WORD, state=tk.NORMAL, height=20)
        self.traceText.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.traceText.yview)
        self.traceText.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Insert traceback into text widget
        user_tips = f"""DIAGNOSTICS:

{self.exception.args[0] if self.exception.args else 'An error occurred.'}

====================

{self.exception.callstack}"""
        self.traceText.insert(tk.END, user_tips)
        self.traceText.configure(state=tk.DISABLED)  # Make text widget read-only
        self.logger.error(user_tips)
        # actions
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        report_btn = ttk.Button(button_frame, text="Report", command=self.on_btn_report)
        report_btn.pack(side=tk.LEFT, padx=5, pady=5)
        copy_btn = ttk.Button(button_frame, text="Copy", command=lambda: self.on_btn_copy(user_tips))
        copy_btn.pack(side=tk.LEFT, padx=5, pady=5)
        help_btn = ttk.Button(button_frame, text="Help?", command=self.on_btn_help)
        help_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        # events
        # give hotkey instead of close button
        self.bind("<Escape>", lambda e: self.destroy())

    def on_btn_report(self):
        """
        - subclass this to report the error to the developer
        - possible imps: send email, open a bug report page, etc.
        """
        if not self.reporter:
            Prompt(self.master, self.logger).warning('No report function is bound. skipped.')
            return
        self.reporter.func(self.exception, self.reporter.cookie)

    def on_btn_copy(self, text):
        """Copy the text content to the clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except Exception as e:
            Prompt(self.master, self.logger).error(type(e), f'Failed to copy to clipboard: {e}.', 'Press Report to send log to dev.', confirm=True)

    def on_btn_help(self):
        """Open the help page on given topic (exception type)."""
        url = self.errHelpMap.get(err := type(self.exception).__name__)
        if not url:
            Prompt(self.master, self.logger).info(f"Undefined error; Press Report button to notify dev team.")
            return
        # file path or web url?
        is_local_file = osp.isfile(url)
        assert url.startswith('http') or url.startswith('www') or is_local_file
        util.open_in_browser(url, islocal=is_local_file)

    def bind_reporter(self, func, cookie=None):
        """
        - report function accepts exception object and user messages (cookie)
        - cookie can contain extended diagnostics such as a session folder, dump files, etc.
        """
        self.reporter = types.SimpleNamespace(func=func, cookie=cookie)

    def bind_helper(self, help_map):
        """
        - help map is a dict of exception type and help url
        - url can be a local file or a web page
        """
        self.errHelpMap = help_map


class NumberEntry(Entry):
    def __init__(self, master: Page, key, text, default, doc, presetable=True, minmax=(float('-inf'), float('inf')), datatype=tk.IntVar, step=1, **kwargs):
        super().__init__(master, key, text, ttk.Frame, default, doc, presetable, **kwargs)
        self.isUserTyping = False
        # model-binding
        self.data = self._init_data(datatype)
        # view
        self.field.configure(style='TFrame')
        self.spinbox = ttk.Spinbox(self.field, textvariable=self.data, from_=minmax[0], to=minmax[1], increment=step, style='TSpinbox')
        self.spinbox.grid(row=0, column=0, padx=(0, 5))  # Adjust padx value
        if not (is_infinite := minmax[0] in (float('-inf'), float('inf')) or minmax[1] in (float('-inf'), float('inf'))):
            self.sliderRatio = tk.DoubleVar(value=(self.data.get() - minmax[0]) / (minmax[1] - minmax[0]))
            self.slider = ttk.Scale(self.field, from_=0.0, to=1.0, orient="horizontal", variable=self.sliderRatio, command=self.on_scale_changed, style='Horizontal.TScale')
            self.slider.grid(row=0, column=1, sticky="ew")
            self.slider.bind("<ButtonRelease-1>", self.on_scale_clicked)
        self.spinbox.bind('<KeyPress>', self.on_start_typing)
        self.spinbox.bind('<KeyRelease>', self.on_stop_typing)
        self.spinbox.bind('<FocusOut>', self.validate_data)

    def set_data(self, value):
        self.data.set(value)
        if hasattr(self, 'sliderRatio'):
            self._sync_scale_with_spinbox()

    def on_start_typing(self, event):
        self.isUserTyping = True

    def on_stop_typing(self, event):
        self.isUserTyping = False

    def set_tracer(self, handler):
        """
        - ignore "write" event while user types into spinbox to avoid invalid data
        - leave validation to out-of-focus event
        """

        def _mouse_tweak_handler(name, var, index, mode):
            if self.isUserTyping:
                return
            handler(name, var, index, mode)

        self.data.trace_add('write', callback=lambda name, index, mode, var=self.data: _mouse_tweak_handler(name, var, index, mode))

    def _sync_scale_with_spinbox(self):
        self.sliderRatio.set((self.data.get() - self.spinbox['from']) / (self.spinbox['to'] - self.spinbox['from']))

    def on_scale_changed(self, ratio):
        raise NotImplementedError('subclass this!')

    def on_scale_clicked(self, event):
        """
        - must ensure inf is not passed in
        - must bind to ButtonRelease-1 to avoid slider malfunction when dragging
        - update_idletasks() redraws slider and flush all pending events, thus reflects recent changes in its look
        - otherwise, it may jump b/w left/right ends when clicking
        """
        relative_x = event.x / (scale_width := self.slider.winfo_width())
        self.slider.set(relative_x)
        self.slider.update_idletasks()

    def validate_data(self, event=None):
        """
        - validate after user focuses out (tab key or mouse click into another entry)
        - ensure the value is a number within the range
        - ignore scenarios of deleting and cleaning up
        - otherwise reset to default
        """
        value = safe_get_number(self.data)
        if not util.is_number_text(str(value)):
            self._alert_and_refocus(value, f'{self.text} ({value}) is not a number')
            return False
        # range check
        minval = self.spinbox.config('from')[4]
        maxval = self.spinbox.config('to')[4]
        try:
            if not (minval <= value <= maxval):
                self._alert_and_refocus(value, f'{self.text} ({value}) is outside range: [{minval}, {maxval}]')
                return False
        except ValueError as e:
            self._alert_and_refocus(value, f'{self.text} ({value}) triggerd unknown error: {e}')
            return False
        if hasattr(self, 'sliderRatio'):
            self._sync_scale_with_spinbox()
        return True

    def _alert_and_refocus(self, value, err_msg):
        Globals.root.bell()
        util.alert(err_msg, 'ERROR')
        Globals.root.after(100, lambda: self.spinbox.focus_set())


class IntEntry(NumberEntry):
    """
    - show slider for finite numbers only
    - ttk.Scale is intended for a ratio only; the handle does not move for negative numbers
    - must bind a separate variable to the slider to ensure slider-clicking works
    """

    def __init__(self, master: Page, key, text, default, doc, presetable=True, minmax=(float('-inf'), float('inf')), step=1, **kwargs):
        super().__init__(master, key, text, default, doc, presetable, minmax, tk.IntVar, step, **kwargs)

    def on_scale_changed(self, ratio):
        try:
            value_range = self.spinbox['to'] - self.spinbox['from']
            new_value = int(self.spinbox['from'] + float(ratio) * value_range)
            self.data.set(new_value)
        except ValueError as e:
            pass  # Ignore non-integer values


class FloatEntry(NumberEntry):
    """
    - must NOT inherit from IntEntry to avoid slider malfunction
    """

    def __init__(self, master: Page, key, text, default, doc, presetable=True, minmax=(float('-inf'), float('inf')), step=0.1, precision=2, **kwargs):
        super().__init__(master, key, text, default, doc, presetable, minmax, tk.DoubleVar, step, **kwargs)
        self.precision = precision

    def on_scale_changed(self, ratio):
        try:
            value_range = self.spinbox['to'] - self.spinbox['from']
            new_value = self.spinbox['from'] + float(ratio) * value_range
            formatted_value = "{:.{}f}".format(float(new_value), self.precision)
            self.data.set(float(formatted_value))
        except ValueError:
            pass


class SingleOptionEntry(Entry):
    """
    - because most clients of optionEntry use its index instead of string value, e.g., csound oscillator waveform is defined by integer among a list of options
    - we must bind to index instead of value for model-binding
    """

    def __init__(self, master: Page, key, text, options, default, doc, presetable=True, **kwargs):
        super().__init__(master, key, text, ttk.Combobox, default, doc, presetable, values=options, **kwargs)
        # model-binding
        self.data = self._init_data(tk.StringVar)
        self.field.configure(textvariable=self.data, state='readonly', style='TCombobox')
        self.index = tk.IntVar(name='index', value=self.get_selection_index())
        self.field.bind("<<ComboboxSelected>>", self.on_option_selected)

    def layout(self):
        self.pack(fill="y", expand=True, padx=5, pady=5, anchor="w")

    def on_option_selected(self, event):
        new_index = self.get_selection_index()
        self.index.set(new_index)

    def get_options(self):
        return self.field.cget('values')

    def get_selection_index(self):
        # Get the current value from self.data
        current_value = self.data.get()
        try:
            # Return the index of the current value in the options list
            return self.get_options().index(current_value)
        except ValueError:
            # If current value is not in the options list, return -1 or handle appropriately
            return -1
        # return self.get_options().index(self.data.get())

    def set_tracer(self, handler):
        self.index.trace_add('write', callback=lambda name, idx, mode, var=self.index: handler(name, var, idx, mode))

    def validate_data(self):
        return True


class MultiOptionEntry(Entry):
    def __init__(self, master: Page, key, text, options, default, doc, presetable=True, **kwargs):
        super().__init__(master, key, text, ttk.Menubutton, default, doc, presetable, **kwargs)
        self.data = {opt: tk.BooleanVar(name=opt, value=opt in default) for opt in options}
        self.field.configure(text='Select one ore more ...')
        # build option menu
        self.selectAll = tk.BooleanVar(name='All', value=True)
        self.selectNone = tk.BooleanVar(name='None', value=False)
        self.menu = tk.Menu(self.field, tearoff=False, bg='#333', fg='#DDD', bd=1, relief='flat', activebackground='#444', activeforeground='#FFF')
        self.field.configure(menu=self.menu)
        self._build_options()

    def layout(self):
        self.pack(fill="y", expand=True, padx=5, pady=5, anchor="w")

    def get_data(self):
        """
        - selected subset
        """
        return [opt for opt in filter(lambda k: self.data[k].get() == 1, self.data.keys())]

    def set_data(self, values):
        """
        - serialized data: selected subset
        """
        for opt in self.data:
            self.data[opt].set(opt in values)

    def _select_all(self):
        for k, v in self.data.items():
            v.set(True)

    def _select_none(self):
        for k, v in self.data.items():
            v.set(False)

    def set_tracer(self, handler):
        for opt in self.data:
            self.data[opt].trace_add('write', callback=lambda name, idx, mode, var=self.data[opt]: handler(name, var, idx, mode))

    def _build_options(self):
        # keep the order
        self.menu.add_command(label='- All -',
                              command=self._select_all)
        self.menu.add_command(label='- None -',
                              command=self._select_none)
        for opt in self.data:
            self.menu.add_checkbutton(label=opt, variable=self.data[opt], onvalue=True, offvalue=False)

    def validate_data(self):
        return True


class BoolEntry(Entry):
    def __init__(self, master: Page, key, text, default, doc, presetable=True, **kwargs):
        super().__init__(master, key, text, ttk.Checkbutton, default, doc, presetable, **kwargs)
        self.data = self._init_data(tk.BooleanVar)
        self.field.configure(variable=self.data)

    def validate_data(self):
        return True


class TextEntry(Entry):
    def __init__(self, master: Page, key, text, default, doc, presetable=True, **kwargs):
        """there is no ttk.Text"""

        super().__init__(master, key, text, tktext.ScrolledText, default, doc, presetable, height=4, wrap=tk.WORD, undo=True, **kwargs)
        self.data = self._init_data(tk.StringVar)
        self.field.bind("<KeyRelease>", self._on_text_changed)
        self.field.bind("<FocusOut>", self._on_text_changed)
        cmd_key = 'Command' if util.PLATFORM == 'Darwin' else 'Control'
        self.field.bind(f"<{cmd_key}-z>", lambda event: self.undo())
        self.field.bind(f"<Control-y>", lambda event: self.redo())
        self.field.bind("<Command-Shift-z>", lambda event: self.redo())

        self.data.trace_add("write", self._on_data_changed)
        self.field.insert("1.0", default)
        # allow paste
        btn_frame = ttk.Frame(self, padding=0,)
        btn_frame.pack(side='bottom', fill='x', expand=True)
        self.primaryBtn = ttk.Button(btn_frame, text="Paste", command=self.on_primary_action)
        self.primaryBtn.pack(side='left', padx=5, anchor="w")
        self.secondaryBtn = ttk.Button(btn_frame, text="Copy", command=self.on_secondary_action)
        self.secondaryBtn.pack(side='left', padx=5, anchor="w")
        # helper
        self.lastContent = default
        # CAUTION: no way to customize the scrollbar color
        # self.field.vbar['troughcolor'] = '#222'
        self.field.configure(foreground='white', background='#222', insertbackground='white', insertwidth=2)

    def undo(self):
        try:
            self.field.edit_undo()
        except tk.TclError:
            pass  # Handle exception if nothing to undo

    def redo(self):
        try:
            self.field.edit_redo()
        except tk.TclError:
            pass  # Handle exception if nothing to redo

    def _on_data_changed(self, *args):
        """
        - update view on model changes
        """
        self.lastContent = self.data.get()
        if self.field.get("1.0", tk.END).strip() != self.lastContent:
            self.field.delete("1.0", tk.END)
            self.field.insert("1.0", self.lastContent)

    def _on_text_changed(self, event):
        """
        - update model on user editing
        - must avoid feedback loop when text changes are caused by model changes
        """
        current_text = self.field.get("1.0", tk.END).strip()
        if self.lastContent != current_text:
            self.data.set(current_text)
            self.lastContent = current_text

    def on_primary_action(self):
        """
        - replace entry text with clipboard content
        """
        # clear the text field first
        self.field.delete("1.0", tk.END)
        self.field.insert(tk.INSERT, self.field.clipboard_get())

    def on_secondary_action(self):
        """
        - replace entry text with clipboard content
        """
        self.field.clipboard_clear()
        self.field.clipboard_append(self.field.get("1.0", tk.END).strip())


class FileEntry(TextEntry):
    """
    - user can type in a list of paths as text lines, one per line
    - to specify a default file-extension, place it as the head of file_patterns
    - always return a list even when there is only one; so use self.data[0] on app side for a single-file case
    """

    def __init__(self, master: Page, key, path, default, doc, presetable=True, file_patterns=(), start_dir=util.get_platform_home_dir(), **kwargs):
        super().__init__(master, key, path, default, doc, presetable, **kwargs)
        self.filePats = file_patterns
        self.startDir = start_dir
        self._fix_platform_patterns()
        self.primaryBtn.configure(text='Browse ...')
        self.secondaryBtn.configure(text='Open')

    def get_data(self):
        """
        - adapt to single path or path collection
        """
        paths = self.data.get().splitlines()
        return paths[0] if len(paths) == 1 else paths

    def set_data(self, value: typing.Union[list[str], tuple[str], str]):
        data = value[0] if isinstance(value, list) and len(value) == 1 else value
        self.data.set('\n'.join(data)) if isinstance(data, list) else self.data.set(value)
        self._on_data_changed()

    def reset(self):
        lst = self.default if isinstance(self.default, (list, tuple)) else [self.default]
        self.set_data(lst)

    def on_primary_action(self):
        preferred_ext = self.filePats[pattern := 0][ext := 1]
        selected = filedialog.askopenfilename(
            parent=self,
            title="Select File(s)",
            initialdir=self.startDir,
            filetypes=self.filePats,
            defaultextension=preferred_ext
        )
        if user_cancelled := selected == '':
            # keep current
            return
        if multi_selection := isinstance(selected, (tuple, list)):
            selected = '\n'.join(selected)
        self.data.set(selected)
        # memorize last selected file's folder
        self.startDir = osp.dirname(selected)

    def on_secondary_action(self):
        """
        - single file: open in default editor
        - multiple files: open common folder in file explorer
        """
        if not (files := self.get_data()):
            return
        if isinstance(files, str) or len(files) == 1:
            file = files if isinstance(files, str) else files[0]
            util.open_in_editor(file)
            return
        # multiple files
        drvwise_dirs = util.get_drivewise_commondirs(files)
        for d in drvwise_dirs.value():
            util.open_in_editor(d)

    def _fix_platform_patterns(self):
        """
        - macOS demands 0 or at least 2 patterns were given if filetypes is set
        """
        if util.PLATFORM != 'Darwin':
            return
        if len(self.filePats) != 1:
            return
        # on macOS, only one pattern was given, so fix it
        self.filePats = tuple([self.filePats[0], ('All Files', '*')])


class FolderEntry(TextEntry):
    """
    - tkinter supports single-folder selection only
    - multiple folders can be pasted into the text field
    """

    def __init__(self, master: Page, key, path, default, doc, presetable=True, start_dir=util.get_platform_home_dir(), **kwargs):
        super().__init__(master, key, path, default, doc, presetable, **kwargs)
        self.startDir = start_dir
        self.primaryBtn.configure(text='Browse ...')

    def get_data(self):
        paths = self.data.get().splitlines()
        return paths[0] if len(paths) == 1 else paths

    def set_data(self, value: typing.Union[list[str], tuple[str], str]):
        data = value[0] if isinstance(value, list) and len(value) == 1 else value
        self.data.set('\n'.join(data)) if isinstance(data, list) else self.data.set(value)
        self._on_data_changed()
        # print(f'set_data: {self.text=}, {value=}\n')

    def on_primary_action(self):
        selected = filedialog.askdirectory(
            parent=self,
            title="Select Folder(s)",
            initialdir=self.startDir,
        )
        if user_cancelled := selected == '':
            # keep current
            return
        self.data.set(selected)
        # memorize last selected file's folder
        self.startDir = osp.dirname(selected)

    def on_secondary_action(self):
        """
        - single file: open in default editor
        - multiple files: open common folder in file explorer
        """
        if not (folder := self.get_data()):
            return
        util.open_in_editor(folder)


class ReadOnlyEntry(Entry):
    """
    - for displaying read-only data
    - a good example is the output of a task, which is not editable by nature
    """

    def __init__(self, master: Page, key, text, default, doc, **widget_kwargs):
        super().__init__(master, key, text, ttk.Label, default, doc, presetable=False, **widget_kwargs)
        self.data = self._init_data(tk.StringVar)
        # allow copy
        self.btnFrame = ttk.Frame(self, padding=5,)
        self.btnFrame.pack(side='bottom', fill='x', expand=True)
        self.primaryBtn = ttk.Button(self.btnFrame, text="Copy", command=self.on_primary_action)
        self.primaryBtn.pack(side='left', padx=5, anchor="w")

    def set_data(self, value):
        self.data.set(value)
        self.field.configure(text=f'{value}')

    def on_primary_action(self):
        self.field.clipboard_clear()
        self.field.clipboard_append(self.field.cget('text').strip())


class ReadOnlyPathEntry(ReadOnlyEntry):
    def __init__(self, master: Page, key, text, default, doc, **widget_kwargs):
        super().__init__(master, key, text, default, doc, **widget_kwargs)
        # allow copy and navigate
        self.secondaryBtn = ttk.Button(self.btnFrame, text="Open", command=self.on_secondary_action)
        self.secondaryBtn.pack(side='left', padx=5, anchor="w")

    def set_data(self, value: typing.Union[list[str], tuple[str], str]):
        data = value[0] if isinstance(value, list) and len(value) == 1 else value
        self.data.set('\n'.join(data)) if isinstance(data, list) else self.data.set(value)
        self.field.configure(text=f'{self.data.get()}')

    def on_secondary_action(self):
        """
        - label-data returns a tuple
        - one-elem tuple uses element size as its len(tuple), which is confusing
        - so we use text directly
        """
        if not (files := self.field.cget('text')):
            return
        files = files.splitlines()
        if len(files) == 1:
            util.open_in_editor(files[0])
            return
        # multiple files
        drvwise_dirs = util.get_drivewise_commondirs(files)
        for d in drvwise_dirs.value():
            util.open_in_editor(d)


class ListEntry(Entry):
    """
    - add loose items by typing
    - remove items by keystroke: delete key
    - load items from a list file
    - batch-select: shift-select, control-select
    - does not need data binding, data is in listbox itself
    """

    def __init__(self, master: Page, key, text, default, doc, presetable, **kwargs):
        super().__init__(master, key, text, ttk.Frame, default, doc, presetable, **kwargs)
        # table
        lst_frame = ttk.Frame(self.field)
        lst_frame.pack(side="top", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(lst_frame, style='Vertical.TScrollbar')
        self.listBox = tk.Listbox(lst_frame, yscrollcommand=scrollbar.set, selectmode="extended", background='#222', foreground='white', selectbackground='#444', selectforeground='white', font=('Courier', 12))
        scrollbar.configure(command=self.listBox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listBox.pack(side="left", fill="both", expand=True)
        self.listBox.bind('<Double-1>', self.on_edit_selected)
        self.listBox.bind('<Delete>', self.on_delete_selected)
        self.listBox.bind('<BackSpace>', self.on_delete_selected)
        self.listBox.bind('<Control-a>', self.on_select_all)
        # buttons
        btn_frame = ttk.Frame(self.field,)
        btn_frame.pack(side='bottom', fill='x', expand=False)
        self.btnAddItem = ttk.Button(btn_frame, text="Add", command=self.on_add)
        self.btnAddItem.pack(side=tk.LEFT)
        self.menubtnSaveLoad = ttk.Menubutton(btn_frame, text="Save/Load")
        self.menu = tk.Menu(self.menubtnSaveLoad, tearoff=False, bg='#333', fg='#DDD', bd=1, relief='flat', activebackground='#444', activeforeground='#FFF')
        self.menubtnSaveLoad.config(menu=self.menu)
        # Add menu items: user will load more often than save when filling forms, so load is placed first
        self.menu.add_command(label="Load ...", command=self.on_load)
        self.menu.add_command(label="Save ...", command=self.on_save)
        self.menubtnSaveLoad.pack(side=tk.LEFT)
        self.reset()

    def get_data(self):
        return list(self.listBox.get(0, tk.END))

    def set_data(self, data: list):
        self.listBox.delete(0, tk.END)
        for item in data:
            self.listBox.insert(tk.END, item)

    def on_save(self):
        preset_file = filedialog.asksaveasfilename(filetypes=[("TSV files", "*.tsv"), ("CSV files", "*.csv"), ("Text files", "*.lst.txt"), ("List files", "*.list")])
        if not preset_file:
            return
        # 1d list of possible str-dumps of csv/tsv rows
        rows = list(self.listBox.get(0, tk.END))
        ext = osp.splitext(preset_file)[1].lower()
        if ext in ['.tsv', '.csv']:
            delim = ',' if ext == '.csv' else '\t'
            rows = [row.split(delim) for row in rows]
            util.save_dsv(preset_file, rows, delimiter=delim, encoding=util.LOCALE_CODEC)
            return
        util.save_lines(preset_file, rows, addlineend=True, encoding=util.LOCALE_CODEC)

    def on_load(self):
        """
        - assume all list/spreadsheet files are headless
        """
        preset_file = filedialog.askopenfilename(filetypes=[("TSV files", "*.tsv"), ("CSV files", "*.csv"), ("Text files", "*.lst.txt"), ("List files", "*.list")])
        if not preset_file:
            return
        self.listBox.delete(0, tk.END)  # Clear existing items
        ext = osp.splitext(preset_file)[1].lower()
        rows = util.load_dsv(preset_file, delimiter=',' if ext == '.csv' else '\t', encoding=util.LOCALE_CODEC) if ext in ['.tsv', '.csv'] else util.load_lines(preset_file, rmlineend=True, encoding=util.LOCALE_CODEC)
        delim = ',' if ext == '.csv' else '\t'
        for row in rows:
            # save row as string
            if isinstance(row, (list, tuple)):
                row = delim.join(row)
            self.listBox.insert(tk.END, row)

    def on_add(self):
        """
        - assume the first column title is the item's name
        """
        new_item = tkdialog.askstring('New Item', f'Enter text for new item:', parent=self)
        if not new_item:
            return
        self.listBox.insert(tk.END, new_item)

    def on_edit_selected(self, event):
        selected_item = self.listBox.curselection()
        if not selected_item:
            return
        index = selected_item[0]
        item_text = self.listBox.get(index)
        # Pop up a dialog to edit the item
        # item_title = self.table['columns'][0]['text']
        new_text = tkdialog.askstring('Edit Item', "Edit item text:", initialvalue=item_text, parent=self)
        if new_text is not None:
            self.listBox.delete(index)
            self.listBox.insert(index, new_text)

    def on_delete_selected(self, event):
        selected_indices = self.listBox.curselection()
        if not selected_indices:
            return
        next_index = None
        for index in reversed(selected_indices):
            if next_index is None:
                next_index = max(0, index - 1)
            self.listBox.delete(index)
        if next_index is not None and next_index < self.listBox.size():
            self.listBox.selection_set(next_index)
            self.listBox.activate(next_index)
            self.listBox.see(next_index)

    def on_select_all(self, event):
        self.listBox.selection_set(0, tk.END)


class CurveEntry(Entry):
    """
    - draw a 1d-curve as line segments, defined by control points
    - user provides x/y axis range, default to unit range [0, 1]
    - builtin rulers and grid, auto-scales upon resizing the canvas
    - all edit ops, e.g., point CRUD, have callbacks for remote sync
    - outputs a sequence of control point X-Y coordinates
    """

    def __init__(self, master: Page, key, text, default, doc, presetable=True, **widget_kwargs):
        super().__init__(master, key, text, ttk.Frame, default, doc, presetable, **widget_kwargs)
        pass

    def main(self):
        pass
