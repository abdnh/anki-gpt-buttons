from __future__ import annotations

import functools
import json
import sys
from typing import Any

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import *

from . import consts

sys.path.append(str(consts.ADDON_DIR / "vendor"))
from .bulk import BulkCompleter

WEB_BASE = f"/_addons/{mw.addonManager.addonFromModule(__name__)}"


def on_gpt_field_button(editor: Editor, i: int) -> None:
    "This is called when a field editor button (the ones labelled 'GPT') is clicked."

    config = mw.addonManager.getConfig(__name__)
    options = config["field_buttons"][i]
    bulk_completer = BulkCompleter(mw, editor.parentWindow, config)
    if editor.addMode:

        def on_success() -> None:
            editor.loadNoteKeepingFocus()

        bulk_completer.fill_note(options, editor.note, on_success)
    else:
        bulk_completer.process_notes(options, [editor.note])


def on_gpt_field_action(browser: Browser, i: int) -> None:
    "This is called when a field browser action is clicked."

    config = mw.addonManager.getConfig(__name__)
    options = config["field_buttons"][i]
    bulk_completer = BulkCompleter(mw, browser, config)
    notes = [mw.col.get_note(nid) for nid in browser.selected_notes()]
    bulk_completer.process_notes(options, notes)


def on_gpt_preset_button(
    editor: Editor, i: int, fill_prompt: bool | None = None
) -> None:
    "This is called when a preset editor button (the ones labelled 'G1', 'G2', ...) is clicked."

    config = mw.addonManager.getConfig(__name__)
    if fill_prompt is None:
        fill_prompt = not config["run_preset_prompt_immediately"]
    options = config["preset_buttons"][i]
    bulk_completer = BulkCompleter(mw, editor.parentWindow, config)
    if editor.addMode:

        def on_success() -> None:
            editor.loadNoteKeepingFocus()

        bulk_completer.fill_note(options, editor.note, on_success, fill_prompt)
    else:
        bulk_completer.process_notes(options, [editor.note], fill_prompt)


def on_gpt_preset_action(browser: Browser, i: int) -> None:
    "This is called when a preset browser action is clicked."

    config = mw.addonManager.getConfig(__name__)
    fill_prompt = not config["run_preset_prompt_immediately"]
    options = config["preset_buttons"][i]
    bulk_completer = BulkCompleter(mw, browser, config)
    notes = [mw.col.get_note(nid) for nid in browser.selected_notes()]
    bulk_completer.process_notes(options, notes, fill_prompt)


def handle_js_message(
    handled: tuple[bool, Any], message: str, context: Any
) -> tuple[bool, Any]:
    """This is used to update and persist the editor toggles state"""

    if not message.startswith("gpt_buttons:"):
        return handled
    _, subcmd, *options = message.split(":")
    if subcmd == "toggle_override":
        button_idx = int(options[0])
        checked = json.loads(options[1])
        config = mw.addonManager.getConfig(__name__)
        config["field_buttons"][button_idx]["override_contents"] = checked
        mw.addonManager.writeConfig(__name__, config)
    elif subcmd == "toggle_run_immediately":
        checked = json.loads(options[0])
        config = mw.addonManager.getConfig(__name__)
        config["run_preset_prompt_immediately"] = checked
        mw.addonManager.writeConfig(__name__, config)
    return True, None


def add_editor_buttons(buttons: list[str], editor: Editor) -> None:
    "This adds the editor buttons and set shortcuts"

    config = mw.addonManager.getConfig(__name__)
    for i, field_button in enumerate(config["field_buttons"]):
        tip = f"GPT Field Button {i+1}"
        if field_button["description"]:
            tip += f": {field_button['description']}"
        if field_button["editor_shortcut"]:
            tip += f' ({field_button["editor_shortcut"]})'
        buttons.append(
            editor.addButton(
                icon=None,
                cmd=f"gpt_field_button_{i}",
                func=functools.partial(on_gpt_field_button, i=i),
                tip=tip,
                label="GPT",
                keys=field_button["editor_shortcut"],
            )
        )
        checked = ""
        if field_button["override_contents"]:
            checked = "checked"
        toggle = f"<div><input type='checkbox' id='gpt_override' oninput='pycmd(`gpt_buttons:toggle_override:{i}:${{event.target.checked}}`)' {checked}><label for='gpt_override' title='GPT Field Button {i+1}: Override existing contents'><img src='{WEB_BASE}/icons/journal-x.svg'></label></div>"
        buttons.append(toggle)

    for i, preset_button in enumerate(config["preset_buttons"]):
        tip = f"GPT Preset {i+1}: {preset_button['description']}"
        if preset_button["editor_shortcut"]:
            tip += f' ({preset_button["editor_shortcut"]})'
        buttons.append(
            editor.addButton(
                icon=None,
                cmd=f"gpt_preset_button_{i}",
                func=functools.partial(
                    on_gpt_preset_button,
                    i=i,
                ),
                tip=tip,
                label=f"G{i+1}",
                keys=preset_button["editor_shortcut"],
            )
        )
        buttons.append(
            editor.addButton(
                icon=None,
                cmd=f"gpt_preset_run_button_{i}",
                func=functools.partial(on_gpt_preset_button, i=i, fill_prompt=False),
                tip=f"Run GPT Preset {i+1}",
                label="R",
            )
        )

    checked = ""
    if config["run_preset_prompt_immediately"]:
        checked = "checked"
    toggle = f"<div><input type='checkbox' id='gpt_run_immediately' oninput='pycmd(`gpt_buttons:toggle_run_immediately:${{event.target.checked}}`)' {checked}><label for='gpt_run_immediately' title='Run GPT presets immediately'><img src='{WEB_BASE}/icons/send.svg'></label></div>"
    buttons.append(toggle)


def add_browser_menu(browser: Browser) -> None:
    "This adds the Edit > GPT menu with items corresponding to all configured buttons"

    config = mw.addonManager.getConfig(__name__)
    gpt_menu = QMenu("GPT", browser)
    for i, field_button in enumerate(config["field_buttons"]):
        action = QAction(
            f"GPT Field Button {i+1}: {field_button['description']}", gpt_menu
        )
        action.setShortcut(field_button["browser_shortcut"])
        qconnect(
            action.triggered,
            functools.partial(on_gpt_field_action, browser=browser, i=i),
        )
        gpt_menu.addAction(action)
    for i, preset_button in enumerate(config["preset_buttons"]):
        action = QAction(
            f"GPT Preset Button {i+1}: {preset_button['description']}", gpt_menu
        )
        action.setShortcut(preset_button["browser_shortcut"])
        qconnect(
            action.triggered,
            functools.partial(on_gpt_preset_action, browser=browser, i=i),
        )
        gpt_menu.addAction(action)

    browser.form.menuEdit.addMenu(gpt_menu)


mw.addonManager.setWebExports(__name__, r"icons/.*")
gui_hooks.editor_did_init_buttons.append(add_editor_buttons)
gui_hooks.webview_did_receive_js_message.append(handle_js_message)
gui_hooks.browser_menus_did_init.append(add_browser_menu)
