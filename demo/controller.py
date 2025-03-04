"""
DEMO: Form-based UI for realtime control
in addition to features in form.py, with builtin support for:
- binding custom entry-value tracers

Dependencies with installation instructions:
- csound
  - macOS: brew install csound
  - Windows: choco install csound, or download and install binary from https://csound.com/download.html
"""
import os.path as osp
import shutil
import sys
import time
# 3rd party
import kkpyutil as util
import pythonosc.udp_client as osc_client
# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/..'))
import kkpyui as ui


class Controller(ui.FormController):
    """
    - assume csound is installed and in PATH
    - assume csound script is in the same directory as this file
    - script runs OSC server and listens to OSC messages below:
      - kk OSClisten gilisten, "/frequency", "f", gkfreq
      - kk OSClisten gilisten, "/gain", "f", gkgaindb
      - kk OSClisten gilisten, "/oscillator", "i", gkwavetype
      - kk OSClisten gilisten, "/duration", "f", gkdur
      - kk OSClisten gilisten, "/play", "i", gkplay
      - kk OSClisten gilisten, "/stop", "i", gkstop
      - kk OSClisten gilisten, "/quit", "i", gkquit
    """

    def __init__(self, fm=None, model=None, to_block=False):
        super().__init__(fm, model, to_block)
        self.sender = osc_client.SimpleUDPClient('127.0.0.1', 10000)
        self.playing = False
        self.curEngine = None

    def run_task(self, event=None):
        """
        - assume csound has started
        - caller (ui submit action) is responsible for updating model
        """
        if self.playing:
            return False
        if self.curEngine != self.model['engine']:
            self.on_shutdown()
            self.on_startup()
        options = ['Sine', 'Square', 'Sawtooth']
        self.sender.send_message('/oscillator', options.index(self.model['oscillator']))
        self.sender.send_message('/frequency', self.model['frequency'])
        self.sender.send_message('/gain', self.model['gain'])
        self.sender.send_message('/play', 1)
        self.start_progress()
        self.playing = True
        return True

    def on_cancel(self, event=None):
        self.sender.send_message('/play', 0)
        self.stop_progress()
        time.sleep(0.1)
        self.playing = False

    def on_startup(self):
        assert osp.isfile(self.model['engine'])
        cmd = [shutil.which('csound'), self.model['engine'], '-odac']
        util.run_daemon(cmd)
        self.curEngine = self.model['engine']
        # time.sleep(0.8)

    def on_shutdown(self, event=None) -> bool:
        if not super().on_shutdown():
            return False
        if ui.Globals.root.isActive:
            self.on_cancel()
        util.kill_process_by_name('csound')
        return True

    def on_task_done(self):
        self.stop_progress()
        self.playing = False

    def on_freq_changed(self, name, var, index, mode):
        freq = ui.safe_get_number(var)
        print(f'{name=}={freq}, {index=}, {mode=}')
        self.sender.send_message('/frequency', freq)

    def on_gain_changed(self, name, var, index, mode):
        gain = ui.safe_get_number(var)
        print(f'{name=}={gain}, {index=}, {mode=}')
        self.sender.send_message('/gain', gain)

    def on_oscillator_changed(self, name, var, index, mode):
        print(f'{name=}={var.get()}, {index=}, {mode=}')
        self.sender.send_message('/play', 0)
        time.sleep(0.1)
        self.sender.send_message('/oscillator', var.get())
        self.sender.send_message('/play', 1)


def main():
    ui.Globals.root = ui.Root('Controller Demo: Oscillator', (800, 600), osp.join(osp.dirname(__file__), 'icon.png'))
    ui.init_style()
    form = ui.Form(ui.Globals.root, ['general', 'output'])
    # ensure progressbar should not block while waiting
    ctrlr = Controller(form, None, False)
    ui.Globals.root.set_controller(ctrlr)
    ui.Globals.root.bind_events()
    menu = ui.FormMenu(ui.Globals.root, ctrlr)
    pg1 = form.pages['general']
    pg2 = form.pages['output']
    # Adding widgets to pages
    scpt_entry = ui.FileEntry(pg1, 'engine', 'Csound Script', osp.join(osp.dirname(__file__), 'tonegen.csd'), 'Path to Csound script', True, [('Csound Script', '*.csd'), ('All Files', '*.*')])
    oscillator_entry = ui.SingleOptionEntry(pg1, 'oscillator', "Oscillator", ['Sine', 'Square', 'Sawtooth', ], 'Square', 'Oscillator waveform types')
    freq_entry = ui.IntEntry(pg1, 'frequency', "Frequency (Hz)", 440, "Frequency of the output signal in Hertz", True, (20, 20000))
    gain_entry = ui.FloatEntry(pg1, 'gain', "Gain (dB)", -16.0, "Gain of the output signal in dB", True, (-48.0, 0.0), 1.0, 2)
    oscillator_entry.set_tracer(ctrlr.on_oscillator_changed)
    freq_entry.set_tracer(ctrlr.on_freq_changed)
    gain_entry.set_tracer(ctrlr.on_gain_changed)
    action_bar = ui.FormActionBar(ui.Globals.root, ctrlr)
    wait_bar = ui.WaitBar(ui.Globals.root, ctrlr)
    ui.Globals.root.mainloop()


if __name__ == "__main__":
    main()
