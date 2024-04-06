# kkpyui

Tkinter-based GUI widget library for building small tool applications

## Motivation

- Small GUI tools come in handy in experiments and ad-hoc productivity boosts

- Full-fledged GUI toolkits such as GTK, Qt, web-app frameworks are often too heavy for these purposes

- Python is my go-to dev language. Its bundled Tkinter (with its `ttk` ) in theory is well-suited for small tool development, but it is often criticized for being outdated and too clunky to use; however, it remains attractive for distribution convenience

- This project thus aims to improve the dev experience of Tkinter for developing small tools. The approach is to create a thin wrapper and iron flat some cross-platform glitches, hoping to reduce boilerplates in appplication code

## Features

- A set of building blocks for creating single-page form UI, with built-in data-binding

- Model-View-Controller architecture

- Per-entry validation, default value, reset, tracer, and help doc

- Saving and loading all form entries as presets

## Demo
```sh
cd /path/to/kkpyui
poetry install

# run form demo
poetry run python demo/form.py

# run controller demo, requireing Csound to be installed and in PATH
poetry run python demo/controller.py
```
