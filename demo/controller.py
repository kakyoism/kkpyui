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
import sys
import time
# 3rd party
import kkpyutil as util
import pythonosc.udp_client as osc_client
# project
_script_dir = osp.abspath(osp.dirname(__file__))
sys.path.insert(0, repo_root := osp.abspath(f'{_script_dir}/../src'))
import kkpyui as ui


def main():
    class OscillatorController(ui.FormController):
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

        def __init__(self, fm=None, model=None):
            super().__init__(fm, model)
            self.sender = osc_client.SimpleUDPClient('127.0.0.1', 10000)
            self.initialized = False
            self.playing = False

        def run_task(self, event=None):
            """
            - assume csound has started
            """
            if self.playing:
                return False
            self.update()
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
            self.update()
            cmd = ['csound', self.model['engine'][0], '-odac']
            util.run_daemon(cmd)
            # time.sleep(0.8)

        def on_shutdown(self, event=None) -> bool:
            if not super().on_shutdown():
                return False
            self.on_cancel()
            util.kill_process_by_name('csound')
            return True

        def on_freq_changed(self, name, var, index, mode):
            print(f'{name=}={var.get()}, {index=}, {mode=}')
            self.sender.send_message('/frequency', var.get())

        def on_gain_changed(self, name, var, index, mode):
            print(f'{name=}={var.get()}, {index=}, {mode=}')
            self.sender.send_message('/gain', var.get())

        def on_oscillator_changed(self, name, var, index, mode):
            print(f'{name=}={var.get()}, {index=}, {mode=}')
            self.sender.send_message('/play', 0)
            time.sleep(0.1)
            self.sender.send_message('/oscillator', var.get())
            self.sender.send_message('/play', 1)

    ui.Globals.root = ui.Root('Controller Demo: Oscillator', (800, 600), osp.join(osp.dirname(__file__), 'icon.png'))
    form = ui.Form(ui.Globals.root, ['general'])
    ctrlr = OscillatorController(form)
    ui.Globals.root.set_controller(ctrlr)
    ui.Globals.root.bind_events()
    menu = ui.FormMenu(ui.Globals.root, ctrlr)
    page = form.pages['general']
    # Adding widgets to pages
    scpt_entry = ui.FileEntry(page, 'engine', 'Csound Script', osp.join(osp.dirname(__file__), 'tonegen.csd'), 'Path to Csound script', [('Csound Script', '*.csd'), ('All Files', '*.*')])
    oscillator_entry = ui.SingleOptionEntry(page, 'oscillator', "Oscillator", ['Sine', 'Square', 'Sawtooth', ], 'Square', 'Oscillator waveform types')
    freq_entry = ui.IntEntry(page, 'frequency', "Frequency (Hz)", 440, "Frequency of the output signal in Hertz", (20, 20000))
    gain_entry = ui.FloatEntry(page, 'gain', "Gain (dB)", -16.0, "Gain of the output signal in dB", (-48.0, 0.0), 1.0, 2)
    oscillator_entry.set_tracer(ctrlr.on_oscillator_changed)
    freq_entry.set_tracer(ctrlr.on_freq_changed)
    gain_entry.set_tracer(ctrlr.on_gain_changed)
    action_bar = ui.FormActionBar(ui.Globals.root, ctrlr)
    wait_bar = ui.WaitBar(ui.Globals.root, ui.Globals.progressQueue)
    wait_bar.poll()
    ui.Globals.root.mainloop()


if __name__ == "__main__":
    main()
