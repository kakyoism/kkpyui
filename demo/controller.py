"""
DEMO: Form-based UI for realtime control
in addition to features in form.py, with builtin support for:
- binding custom entry-value tracers

Dependencies with installation instructions:
- csound
  - macOS: brew install csound
  - Windows: winget install csound, or, choco install csound
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
        kk OSClisten gilisten, "/frequency", "f", gkfreq
        kk OSClisten gilisten, "/gain", "f", gkgaindb
        kk OSClisten gilisten, "/oscillator", "i", gkwavetype
        kk OSClisten gilisten, "/duration", "f", gkdur
        kk OSClisten gilisten, "/play", "i", gkplay
        kk OSClisten gilisten, "/stop", "i", gkstop
        kk OSClisten gilisten, "/quit", "i", gkquit
        """

        def __init__(self, fm=None, model=None):
            super().__init__(fm, model)
            self.sender = osc_client.SimpleUDPClient('127.0.0.1', 10000)
            self.playing = False

        def submit(self, event=None):
            if self.playing:
                return False
            self.update()
            cmd = ['csound', self.model['General']['Csound Script'], '-odac']
            util.run_daemon(cmd)
            # wait for csound to start
            time.sleep(1)
            options = ['Sine', 'Square', 'Sawtooth']
            self.sender.send_message('/oscillator', options.index(self.model['General']['Oscillator']))
            self.sender.send_message('/frequency', self.model['General']['Frequency (Hz)'])
            self.sender.send_message('/gain', self.model['General']['Gain (dB)'])
            self.sender.send_message('/play', 1)
            ui.Globals.progressQueue.put(('/start', 0, 'Playing ...'))
            self.playing = True
            return True

        def cancel(self, event=None):
            self.sender.send_message('/play', 0)
            ui.Globals.progressQueue.put(('/stop', 100, 'Stopped'))
            time.sleep(1)
            self.playing = False

        def on_freq(self, name, var, index, mode):
            print(f'{name=}={var.get()}, {index=}, {mode=}')
            self.sender.send_message('/frequency', var.get())

        def on_gain(self, name, var, index, mode):
            print(f'{name=}={var.get()}, {index=}, {mode=}')
            self.sender.send_message('/gain', var.get())

        def on_oscillator(self, name, var, index, mode):
            print(f'{name=}={var.get()}, {index=}, {mode=}')
            self.sender.send_message('/play', 0)
            time.sleep(0.1)
            self.sender.send_message('/oscillator', var.get())
            self.sender.send_message('/play', 1)

    ui.create_window('Controller Example', (800, 600))
    form = ui.Form(ui.Globals.root)
    form.layout()
    ctrlr = OscillatorController(form)
    menu = ui.FormMenu(ui.Globals.root, ctrlr)
    menu.init(ui.Globals.root)
    # Creating groups
    page = ui.Page(form.entryPane, "General")
    page.layout()

    # Adding widgets to groups
    scpt_entry = ui.TextEntry(page, 'Csound Script', osp.join(osp.dirname(__file__), 'tonegen.csd'), 'Path to Csound script')
    oscillator_entry = ui.OptionEntry(page, "Oscillator", ['Sine', 'Square', 'Sawtooth',], 'Square', 'Oscillator waveform types')
    freq_entry = ui.IntEntry(page, "Frequency (Hz)", 440, "Frequency of the output signal in Herz", (20, 20000))
    gain_entry = ui.FloatEntry(page, "Gain (dB)", -6.0, "Gain of the output signal in dB", (-48.0, 0.0), 2, 1.0)
    oscillator_entry.set_tracer(ctrlr.on_oscillator)
    freq_entry.set_tracer(ctrlr.on_freq)
    gain_entry.set_tracer(ctrlr.on_gain)
    page.add([scpt_entry, oscillator_entry, freq_entry, gain_entry])
    form.init([page])
    form.layout()
    action_bar = ui.OnOffActionBar(ui.Globals.root, ctrlr)
    action_bar.layout()
    wait_bar = ui.WaitBar(ui.Globals.root, ui.Globals.progressQueue)
    wait_bar.layout()
    wait_bar.poll()
    ui.Globals.root.mainloop()


if __name__ == "__main__":
    main()
