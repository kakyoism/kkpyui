import json
import os.path as osp
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox as tkmsgbox
# 3rd party
import kkpyutil as util


class Globals:
    root = None
    progressQueue = queue.Queue()


def _validate_int(value_after_input, user_input, widget_name):
    return _validate_number(value_after_input, user_input, widget_name, int)


def _validate_float(value_after_input, user_input, widget_name):
    return _validate_number(value_after_input, user_input, widget_name, float)


def _validate_number(value_after_input, user_input, widget_name, data_type):
    """
    - ttk.spinbox does not support paste over selection; pasted content always prepends
    - so pasting always fails number validation in spinbox
    """
    # allow '-6.' and append 0 to fix format
    if truncated_float := data_type == float and value_after_input.endswith('.') and util.is_float_text(value_after_input):
        value_after_input += '0'
        return True
    # '-' is not a valid number and will fail here, beware erase digits in a row with backspace
    if not util.is_number_text(value_after_input) or value_after_input == '':
        Globals.root.bell()
        return False
    raw_min = Globals.root.nametowidget(widget_name).config('from')[4]
    raw_max = Globals.root.nametowidget(widget_name).config('to')[4]
    minval = raw_min if raw_min in (float('-inf'), float('inf')) else data_type(raw_min)
    maxval = raw_max if raw_max in (float('-inf'), float('inf')) else data_type(raw_max)
    try:
        if not (minval <= data_type(value_after_input) <= maxval):
            Globals.root.bell()
            util.alert(f"""New value {value_after_input} would fall outside of range: [{minval}, {maxval}]
Change skipped""", 'ERROR')
            return False
    except ValueError as e:
        Globals.root.bell()
        return False
    return True


class Root(tk.Tk):
    def __init__(self, title, size=(800, 600), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        screen_size = (self.winfo_screenwidth(), self.winfo_screenheight())
        self.geometry('{}x{}+{}+{}'.format(
            size[0],
            size[1],
            int(screen_size[0] / 2 - size[0] / 2),
            int(screen_size[1] / 2 - size[1] / 2))
        )
        self.validateIntCmd = (self.register(_validate_int), '%P', '%S', '%W')
        self.validateFloatCmd = (self.register(_validate_float), '%P', '%S', '%W')
        self._auto_focus()

    def bind_events(self, controller):
        """
        - controller interface must implement:
          - ENTER key event: default action
          - ESC key event: cancel/negate default action
          - Window X button event: quit
        - refer to Inter-Client Communication Conventions Manual ICCCM for possible window events
        """
        self.bind("<Return>", controller.submit)
        self.bind("<Escape>", lambda event: controller.cancel(event))
        # Expose: called even when slider is dragged, so we don't use it
        # Map: triggered when windows are visible
        self.bind('<Map>', lambda event: controller.init(event))
        self.bind('<Destroy>', lambda event: controller.term(event))
        # bind X button to quit the program
        self.protocol('WM_DELETE_WINDOW', controller.quit)

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


class Prompt:
    """
    - must use within tkinter mainloop
    - otherwise the app will freeze upon confirmation
    """

    def __init__(self, logger=None):
        self.logger = logger or util.glogger

    def info(self, msg, confirm=True):
        """Prompt with info."""
        self.logger.info(msg)
        if confirm:
            tkmsgbox.showinfo('Info', msg, icon='info')

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
        return tkmsgbox.askyesno('Warning', msg, icon='warning')

    def error(self, errclass, detail, advice, confirm=True):
        """
        - for problems with significant impact
         - the program will crash immediately
        """
        msg = f"""\
Detail:
{detail}

Advice:
{advice}

Will crash"""
        self.logger.error(msg)
        if confirm:
            tkmsgbox.showerror('Error', msg, icon='error')
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
            self.canvas.configure(scrollregion=(0, 0, width, height))
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.frame.winfo_reqwidth())

        def _configure_canvas(event):
            # update the inner frame's width to fill the canvas
            if self.frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.itemconfigure(frame_id, width=self.canvas.winfo_width())

        super().__init__(master, *args, **kwargs)
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.frame = ttk.Frame(self.canvas)
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
        self.navPane = ttk.Frame(self, width=200)
        self.navPane.pack_propagate(False)  # Prevent the widget from resizing to its contents
        # Create a new frame for the search box and treeview
        search_box = ttk.Frame(self.navPane)
        search_box.pack(side="top", fill="x")
        self.searchEntry = ttk.Entry(search_box)
        self.searchEntry.pack(side="left", fill="x", expand=True)
        self.searchEntry.bind("<KeyRelease>", self.filter_entries)
        self.searchEntry.bind("<Control-BackSpace>", self._on_clear_search)
        # Place the treeview below the search box
        self.tree = ttk.Treeview(self.navPane, show="tree")
        self.tree.heading("#0", text="", anchor="w")  # Hide the column header
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.update_entries)
        # Right panel: entries in page
        self.entryPane = ScrollFrame(self)
        # build form with navbar and page frame
        self.add(self.navPane, weight=0)
        self.add(self.entryPane, weight=1)
        self.pages = {title.lower(): Page(self.entryPane.frame, title.title()) for title in page_titles}
        self.init()
        self.layout()

    def layout(self):
        self.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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


class Entry(ttk.Frame):
    """
    - used as user input, similar to CLI arguments
    - widget must belong to a group
    - groups form a tree to avoid overloading parameter panes
    - groups also improve SNR by prioritizing frequently-tweaked parameters
    - page is responsible for lay out entries
    """

    def __init__(self, master: Page, text, widget_constructor, default, doc, **widget_kwargs):
        super().__init__(master)
        assert isinstance(self.master, Page)
        self.master.add([self])
        self.text = text
        self.default = default
        # model-binding
        self.data = None
        # title
        self.label = ttk.Label(self, text=self.text, cursor='hand2')
        self.label.pack(expand=True, padx=5, pady=2, anchor="w")
        self.label.bind("<Double-Button-1>", lambda e: tkmsgbox.showinfo("Help", doc))
        # field
        self.field = widget_constructor(self, **widget_kwargs)
        self.columnconfigure(0, weight=1)
        self.field.pack(expand=True, padx=5, pady=2, anchor="w")
        # context menu
        self.contextMenu = tk.Menu(self, tearoff=0)
        # use a context menu instead of direct clicking to avoid accidental reset
        self.contextMenu.add_command(label="Reset", command=self.reset)
        # maximize context-menu hitbox
        self.field.bind("<Button-2>", self.show_context_menu)
        self.label.bind("<Button-2>", self.show_context_menu)

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


class FormMenu(tk.Menu):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        assert isinstance(self.master, tk.Tk)
        self.master.configure(menu=self)
        self.fileMenu = tk.Menu(self, tearoff=False)
        self.fileMenu.add_command(label="Load Preset ...", command=self.on_load_preset)
        self.fileMenu.add_command(label="Save Preset ...", command=self.on_save_preset)
        self.fileMenu.add_command(label="Exit", command=self.on_quit)
        self.add_cascade(label="File", menu=self.fileMenu)
        self.controller = controller

    def on_load_preset(self):
        preset = filedialog.askopenfilename(title="Load Preset", filetypes=[
            # tkinter openfile dialog filter does not accept middlename,
            # so *.preset.json won't work here
            ("Preset Files", "*.json"),
        ])
        if preset:
            self.controller.load(preset)

    def on_save_preset(self):
        preset = filedialog.asksaveasfilename(title="Save Preset", filetypes=[
            ("Preset Files", "*.preset.json"),
        ])
        if preset:
            self.controller.save(preset)

    def on_quit(self):
        self.controller.quit(None)


class FormController:
    """
    - observe all entries and update model
    - both form and realtime apps can use this class,
    - realtime apps can set arg-tracers while form apps can use submit() to update model
    """

    def __init__(self, form=None, model=None):
        self.form = form
        self.model = model
        self.set_progress = lambda title, progress, description: Globals.progressQueue.put((title, progress, description))

    def update(self):
        self.model = {pg.get_title(): {entry.text: entry.get_data() for entry in pg.winfo_children()} for pg in self.form.pages.values()}

    def load(self, preset):
        """
        - model includes input and config
        - input is runtime data that changes with each run
        - only config will be saved/loaded as preset
        """
        config = util.load_json(preset)
        for title, page in self.form.pages.items():
            for entry in page.winfo_children():
                try:
                    entry.set_data(config[title][entry.text])
                except KeyError:
                    pass

    def save(self, preset):
        """
        - only config is saved
        - input always belongs to group "input"
        """
        self.update()
        config = {pg.get_title(): {entry.text: entry.get_data() for entry in pg.winfo_children()} for title, pg in self.form.pages.items() if title != "input"}
        util.save_json(preset, config)

    def reset(self):
        for pg in self.form.pages.values():
            for entry in pg.winfo_children():
                entry.reset()

    def submit(self, event=None):
        """
        - subclass this to implement custom logic
        """
        self.update()
        # lambda wrapper ensures "self" is captured by threading as a context
        # otherwise ui thread still blocks
        threading.Thread(target=lambda: self.run_background(), daemon=True).start()

    def run_background(self):
        """
        - override this in app
        - run in background thread to avoid blocking UI
        """
        raise NotImplementedError('subclass this!')

    def cancel(self, event=None):
        """
        - for form-filling case, we quit window on cancelling
        - override this in app
        """
        self.quit()

    def quit(self, event=None):
        """
        - CAUTION:
          - for sharing binding between menu, x-button, and another ui for quitting
          - although usually we avoid view ops in controller
        - override term() in app
        """
        self.term()
        self.form.master.quit()

    def init(self, event=None):
        """
        - binding of <Expose> event as logical initialization
        - called after mainloop() started, i.e., when window is partially visible
        - controller can start retrieving entries
        - override this in app
        """
        pass

    def term(self, event=None):
        """
        - binding of <Destroy> event as logical termination
        - called AFTER triggering WM_DELETE_WINDOW
        - override this in app
        """
        pass


class FormActionBar(ttk.Frame):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # action logic
        self.controller = controller
        # occupy the entire width
        # new buttons will be added to the right
        self.resetBtn = ttk.Button(self, text="Reset", command=self.on_reset_entries)
        self.separator = ttk.Separator(self, orient="horizontal")
        # Create Cancel and Submit buttons
        self.cancelBtn = ttk.Button(self, text="Cancel", command=self.on_cancel)
        self.submitBtn = ttk.Button(self, text="Submit", command=self.on_submit, cursor='hand2')
        # layout: keep the order
        self.separator.pack(fill="x")
        # left-most must pack after separator to avoid occluding the border
        self.resetBtn.pack(side="left", padx=10, pady=5)
        self.submitBtn.pack(side="right", padx=10, pady=10)
        self.cancelBtn.pack(side="right", padx=10, pady=10)
        self.layout()

    def layout(self):
        self.pack(side="bottom", fill="x")

    def submit(self, event=None):
        """for debugging only"""
        self.controller.update()
        formatted_data = json.dumps(self.controller.model, indent=4)
        tkmsgbox.showinfo("Submitted Data", formatted_data)

    def on_reset_entries(self, event=None):
        self.controller.reset()

    def on_cancel(self, event=None):
        self.controller.cancel()

    def on_submit(self, event=None):
        self.controller.submit()


class OnOffActionBar(FormActionBar):
    def __init__(self, master, controller, *args, **kwargs):
        super().__init__(master, controller, *args, **kwargs)
        self.submitBtn.configure(text='Start')
        self.cancelBtn.configure(text='Stop')


class WaitBar(ttk.Frame):
    """
    - app must run in worker thread to avoid blocking UI
    - when using subprocess to run a blackbox task, use indeterminate mode cuz there is no way to pass progress back
    - protocol: tuple(stage, progress, description), where stage is program instruction, description is for display
    - TODO: use IPC for cross-language open-source tasks
    """

    def __init__(self, master, progress_queue, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.queue = progress_queue
        self.stage = tk.StringVar(name='stage', value='')
        self.bar = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.label = ttk.Label(self.bar, textvariable=self.stage, text='...', foreground='white', background='black')
        self.layout()

    def layout(self):
        """
        - overlay label on top of bar
        """
        self.bar.pack(side="right", fill="x", expand=True)
        self.label.place(relx=0.5, rely=0.5, anchor='center')
        self.pack(side='bottom', fill='both', expand=False)

    def poll(self, wait_ms=50):
        """
        - app pushes special messages to mark progress start/stop
        """
        while self.queue.qsize():
            msg = self.queue.get(0)
            cmd = msg[0]
            if cmd == '/start':
                self.bar.start()
            elif cmd == '/stop':
                self.bar.stop()
            else:
                raise NotImplementedError(f'Unexpected progress instruction: {cmd}')
        self.after(wait_ms, self.poll)


class ProgressBar(WaitBar):
    def __init__(self, master, progress_queue, *args, **kwargs):
        super().__init__(master, progress_queue, *args, **kwargs)
        self.progress = tk.DoubleVar(name='progress', value=0.)
        self.bar.configure(variable=self.progress, mode='determinate')
        self.layout()

    def poll(self, wait_ms=50):
        """
        - Periodically check for messages from worker thread.
        """
        while self.queue.qsize():
            try:
                cmd, value, text = self.queue.get_nowait()
                if cmd == '/start':
                    self.bar.start()
                elif cmd == '/stop':
                    self.bar.stop()
                elif cmd == '/processing':
                    self.progress.set(value)
                self.stage.set(text)  # Update the label text
            except queue.Empty:
                pass
        self.after(wait_ms, self.poll)


class IntEntry(Entry):
    """
    - show slider for finite numbers only
    - ttk.Scale is intended for a ratio only; the handle does not move for negative numbers
    - must bind a separate variable to the slider to ensure slider-clicking works
    """
    def __init__(self, master: Page, text, default, doc, minmax=(float('-inf'), float('inf')), step=1, **kwargs):
        super().__init__(master, text, ttk.Frame, default, doc, **kwargs)
        # model-binding
        self.data = self._init_data(tk.IntVar)
        # view
        self.spinbox = ttk.Spinbox(self.field, textvariable=self.data, from_=minmax[0], to=minmax[1], increment=step, validate='all', validatecommand=Globals.root.validateIntCmd)
        self.spinbox.grid(row=0, column=0, padx=(0, 5))  # Adjust padx value
        if not (is_infinite := minmax[0] in (float('-inf'), float('inf')) or minmax[1] in (float('-inf'), float('inf'))):
            self.ratio = tk.DoubleVar(value=(self.data.get() - minmax[0]) / (minmax[1] - minmax[0]))
            self.slider = ttk.Scale(self.field, from_=0.0, to=1.0, orient="horizontal", variable=self.ratio, command=self.on_scale_changed)
            self.slider.grid(row=0, column=1, sticky="ew")
            self.slider.bind("<Button-1>", self.on_scale_clicked)

    def set_data(self, value):
        self.data.set(value)
        if hasattr(self, 'ratio'):
            self._sync_scale_with_spinbox()

    def _sync_scale_with_spinbox(self):
        self.ratio.set((self.data.get() - self.spinbox['from']) / (self.spinbox['to'] - self.spinbox['from']))

    def on_scale_changed(self, ratio):
        new_value = None
        try:
            self.ratio.set(ratio)
            value_range = self.spinbox['to'] - self.spinbox['from']
            new_value = int(self.spinbox['from'] + float(ratio) * value_range)
            self.data.set(new_value)
        except ValueError:
            pass  # Ignore non-integer values

    def on_scale_clicked(self, event):
        """
        - must ensure inf is not passed in
        - update_idletasks() redraws slider and flush all pending events, thus reflects recent changes in its look
        - otherwise, it may jump b/w left/right ends when clicking
        """
        relative_x = event.x / (scale_width := self.slider.winfo_width())
        self.on_scale_changed(relative_x)
        self.slider.update_idletasks()


class FloatEntry(Entry):
    """
    - must NOT inherit from IntEntry to avoid slider malfunction
    """
    def __init__(self, master: Page, text, default, doc, minmax, step=0.1, precision=2, **kwargs):
        super().__init__(master, text, ttk.Frame, default, doc, **kwargs)
        self.precision = precision
        # model-binding
        self.data = self._init_data(tk.DoubleVar)
        # view
        self.spinbox = ttk.Spinbox(self.field, textvariable=self.data, from_=minmax[0], to=minmax[1], increment=step, validate='all', validatecommand=Globals.root.validateFloatCmd)
        self.spinbox.grid(row=0, column=0, padx=(0, 5))  # Adjust padx value
        if not (is_infinite := minmax[0] in (float('-inf'), float('inf')) or minmax[1] in (float('-inf'), float('inf'))):
            self.ratio = tk.DoubleVar(value=(self.data.get() - minmax[0]) / (minmax[1] - minmax[0]))
            self.slider = ttk.Scale(self.field, from_=0.0, to=1.0, orient="horizontal", variable=self.ratio, command=self.on_scale_changed)
            self.slider.grid(row=0, column=1, sticky="ew")
            self.slider.bind("<Button-1>", self.on_scale_clicked)

    def set_data(self, value):
        self.data.set(value)
        if hasattr(self, 'ratio'):
            self._sync_scale_with_spinbox()

    def _sync_scale_with_spinbox(self):
        self.ratio.set((self.data.get() - self.spinbox['from']) / (self.spinbox['to'] - self.spinbox['from']))

    def on_scale_changed(self, ratio):
        try:
            value_range = self.spinbox['to'] - self.spinbox['from']
            new_value = self.spinbox['from'] + float(ratio) * value_range
            formatted_value = "{:.{}f}".format(float(new_value), self.precision)
            self.data.set(float(formatted_value))
        except ValueError:
            pass

    def on_scale_clicked(self, event):
        """
        - must ensure inf is not passed in
        """
        relative_x = event.x / (scale_width := self.slider.winfo_width())
        self.slider.set(relative_x)
        self.slider.update_idletasks()


class SingleOptionEntry(Entry):
    """
    - because most clients of optionEntry use its index instead of string value, e.g., csound oscillator waveform is defined by integer among a list of options
    - we must bind to index instead of value for model-binding
    """
    def __init__(self, master: Page, text, options, default, doc, **kwargs):
        super().__init__(master, text, ttk.Combobox, default, doc, values=options, **kwargs)
        # model-binding
        self.data = self._init_data(tk.StringVar)
        self.field.configure(textvariable=self.data, state='readonly')
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


class MultiOptionEntry(Entry):
    def __init__(self, master: Page, text, options, default, doc, **kwargs):
        super().__init__(master, text, ttk.Menubutton, default, doc, **kwargs)
        self.data = {opt: tk.BooleanVar(name=opt, value=opt in default) for opt in options}
        self.field.configure(text='Select one ore more ...')
        # build option menu
        self.selectAll = tk.BooleanVar(name='All', value=True)
        self.selectNone = tk.BooleanVar(name='None', value=False)
        self.menu = tk.Menu(self.field, tearoff=False)
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
            self.data[opt].set(1 if opt in values else 0)

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


class BoolEntry(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        super().__init__(master, text, ttk.Checkbutton, default, doc, **kwargs)
        self.data = self._init_data(tk.BooleanVar)
        self.field.configure(variable=self.data)


class TextEntry(Entry):
    def __init__(self, master: Page, text, default, doc, **kwargs):
        """there is no ttk.Text"""

        super().__init__(master, text, tk.Text, default, doc, height=4, **kwargs)
        self.data = self._init_data(tk.StringVar)
        # because the binding definition below will trigger callbacks,
        # we must avoid feedback loop by setting this flag right before binding
        self._updatingModel = True
        self.field.bind("<<Modified>>", self._on_text_changed)
        self.data.trace_add("write", self._on_data_changed)
        self.field.insert("1.0", default)
        # allow paste
        self.actionBtn = ttk.Button(self, text="Paste", command=self.on_action)
        self.actionBtn.pack(side='bottom', expand=True, padx=5, anchor="w")

    def set_data(self, value):
        super().set_data(value)
        self._on_data_changed()

    def _on_data_changed(self, *args):
        """
        - update view on model changes
        """
        self._updatingModel = True
        seen = self.field.get("1.0", tk.END).strip()
        to_see = self.data.get()
        if seen != to_see:
            self.field.delete("1.0", tk.END)
            self.field.insert("1.0", to_see)
        self._updatingModel = False

    def _on_text_changed(self, event):
        """
        - update model on user editing
        - must avoid feedback loop when text changes are caused by model changes
        """
        if self._updatingModel:
            return
        self.data.set(self.field.get("1.0", tk.END))
        self.field.edit_modified(False)

    def on_action(self):
        """
        - replace entry text with clipboard content
        """
        # clear the text field first
        self.field.delete("1.0", tk.END)
        self.field.insert(tk.INSERT, self.field.clipboard_get())


class FileEntry(TextEntry):
    """
    - user can type in a list of paths as text lines, one per line
    - to specify a default file-extension, place it as the head of file_patterns
    - always return a list even when there is only one; so use self.data[0] on app side for a single-file case
    """
    def __init__(self, master: Page, path, default, doc, file_patterns=(), start_dir=util.get_platform_home_dir(), **kwargs):
        super().__init__(master, path, default, doc, **kwargs)
        self.filePats = file_patterns
        self.startDir = start_dir
        self._fix_platform_patterns()
        self.actionBtn.configure(text='Browse ...')

    def get_data(self):
        return self.data.get().splitlines()

    def on_action(self):
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
    def __init__(self, master: Page, path, default, doc, start_dir=util.get_platform_home_dir(), **kwargs):
        super().__init__(master, path, default, doc, **kwargs)
        self.startDir = start_dir
        self.actionBtn.configure(text='Browse ...')

    def get_data(self):
        return self.data.get().splitlines()

    def on_action(self):
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
