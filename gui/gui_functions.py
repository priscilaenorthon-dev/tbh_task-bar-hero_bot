from functools import partial
from tkinter import Canvas, Frame, Label, Toplevel

import utils.global_variables as gv
from functionality.stash_loop import reset_stash_state, start_periodic_stash_sort, stash_loop
from utils.config import save_data
from wrappers.logging_wrapper import apply_log_level, debug, info, warning

_MIN_REGION_SIZE = 20
_OVERLAY_ALPHA = 0.25


def popup_rectangle_window(button, x, y, width, height):
    """Show current region; click anywhere to close."""
    apply_log_level()
    info("Region preview: opening overlay")
    window, canvas, bar = _create_overlay()
    window.update_idletasks()
    info(
        "Region preview: canvas at screen "
        f"({canvas.winfo_rootx()}, {canvas.winfo_rooty()}) "
        f"size {canvas.winfo_width()}x{canvas.winfo_height()}"
    )
    _draw_region_on_canvas(canvas, x.get(), y.get(), width.get(), height.get())

    def close(_event=None):
        if _event is not None:
            debug(f"Region preview: close at ({_event.x_root}, {_event.y_root})")
        info("Region preview: closed")
        window.destroy()
        button.configure(
            command=partial(popup_rectangle_window, button, x, y, width, height)
        )

    _bind_click_close(window, canvas, bar, close)
    button.configure(command=partial(close))


def open_set_region_drag(x, y, width, height):
    """Fullscreen overlay: left-drag to set search region (screen coordinates)."""
    apply_log_level()
    info("Region draw: opening overlay (dimmed, captures mouse)")
    window, canvas, bar = _create_overlay()
    window.update_idletasks()
    info(
        "Region draw: canvas at screen "
        f"({canvas.winfo_rootx()}, {canvas.winfo_rooty()}) "
        f"size {canvas.winfo_width()}x{canvas.winfo_height()}"
    )
    drag = {"rect_id": None, "start_x": None, "start_y": None}

    if width.get() >= _MIN_REGION_SIZE and height.get() >= _MIN_REGION_SIZE:
        drag["rect_id"] = _draw_region_on_canvas(
            canvas, x.get(), y.get(), width.get(), height.get(), outline="#88ff88"
        )
        info(
            f"Region draw: showing current region "
            f"({x.get()}, {y.get()}) {width.get()}x{height.get()}"
        )
    else:
        info("Region draw: no current region to show — drag a new rectangle")

    def close(_event=None):
        if _event is not None:
            debug(f"Region draw: cancel at ({_event.x_root}, {_event.y_root})")
        info("Region draw: overlay closed")
        window.destroy()

    def on_press(event):
        drag["start_x"] = event.x_root
        drag["start_y"] = event.y_root
        info(f"Region draw: press at screen ({event.x_root}, {event.y_root})")
        if drag["rect_id"] is not None:
            canvas.delete(drag["rect_id"])
            drag["rect_id"] = None
        cx1, cy1 = _screen_to_canvas(canvas, event.x_root, event.y_root)
        debug(f"Region draw: press on canvas ({cx1:.0f}, {cy1:.0f})")
        drag["rect_id"] = canvas.create_rectangle(
            cx1, cy1, cx1, cy1, outline="lime", width=3
        )

    def on_motion(event):
        if drag["rect_id"] is None or drag["start_x"] is None:
            return
        cx1, cy1 = _screen_to_canvas(canvas, drag["start_x"], drag["start_y"])
        cx2, cy2 = _screen_to_canvas(canvas, event.x_root, event.y_root)
        canvas.coords(drag["rect_id"], cx1, cy1, cx2, cy2)
        debug(f"Region draw: drag to screen ({event.x_root}, {event.y_root})")

    def on_release(event):
        if drag["start_x"] is None:
            warning("Region draw: release without press — ignored")
            return
        left = min(drag["start_x"], event.x_root)
        top = min(drag["start_y"], event.y_root)
        region_width = abs(event.x_root - drag["start_x"])
        region_height = abs(event.y_root - drag["start_y"])
        info(
            f"Region draw: release at ({event.x_root}, {event.y_root}) "
            f"→ {region_width}x{region_height} px"
        )
        if region_width < _MIN_REGION_SIZE or region_height < _MIN_REGION_SIZE:
            warning(
                f"Region draw: too small ({region_width}x{region_height}), "
                f"need at least {_MIN_REGION_SIZE}px — try again"
            )
            drag["start_x"] = None
            drag["start_y"] = None
            if drag["rect_id"] is not None:
                canvas.delete(drag["rect_id"])
                drag["rect_id"] = None
            return
        x.set(int(left))
        y.set(int(top))
        width.set(int(region_width))
        height.set(int(region_height))
        info(f"Region draw: applied ({left}, {top}) {region_width}x{region_height}")
        close()

    _bind_drag(window, canvas, bar, on_press, on_motion, on_release)
    window.bind("<Escape>", close)
    info("Region draw: ready — left-click and drag on the dimmed screen (Esc to cancel)")


def _create_overlay():
    """
    Semi-transparent fullscreen overlay.

    Avoids -transparentcolor, which on Windows lets clicks pass through to the
    game/desktop so drag never fires.
    """
    window = Toplevel()
    window.resizable(False, False)
    window.attributes("-fullscreen", True)
    window.attributes("-topmost", True)
    window.attributes("-alpha", _OVERLAY_ALPHA)
    window.configure(bg="#000000")

    bar = Frame(window, bg="#222222", height=36)
    bar.pack(fill="x")
    Label(
        bar,
        text="Drag with left-click to set search region  •  Esc to cancel",
        fg="#eeeeee",
        bg="#222222",
        font=("Segoe UI", 10),
    ).pack(pady=6)

    canvas = Canvas(window, highlightthickness=0, bg="#000000", cursor="crosshair")
    canvas.pack(fill="both", expand=True)
    return window, canvas, bar


def _bind_drag(window, canvas, bar, on_press, on_motion, on_release):
    for widget in (window, canvas, bar):
        widget.bind("<ButtonPress-1>", on_press)
        widget.bind("<B1-Motion>", on_motion)
        widget.bind("<ButtonRelease-1>", on_release)


def _bind_click_close(window, canvas, bar, close):
    for widget in (window, canvas, bar):
        widget.bind("<Button-1>", close)


def _screen_to_canvas(canvas, screen_x, screen_y):
    return screen_x - canvas.winfo_rootx(), screen_y - canvas.winfo_rooty()


def _draw_region_on_canvas(canvas, left, top, width, height, outline="lime"):
    right = left + width
    bottom = top + height
    cx1, cy1 = _screen_to_canvas(canvas, left, top)
    cx2, cy2 = _screen_to_canvas(canvas, right, bottom)
    debug(
        f"Region overlay: draw rect canvas ({cx1:.0f},{cy1:.0f})-({cx2:.0f},{cy2:.0f})"
    )
    return canvas.create_rectangle(cx1, cy1, cx2, cy2, outline=outline, width=3)


def on_closing():
    save_data()
    info("GUI: Saving data")
    info("GUI: Closing")
    gv.root.destroy()


def start_stash(button):
    apply_log_level()
    gv.continue_stash = True
    reset_stash_state()
    button.configure(text="Stop Stash", command=partial(stop_stash, button))
    stash_loop()
    start_periodic_stash_sort()


def stop_stash(button):
    gv.continue_stash = False
    gv.status_message = "Stopped"
    info("Process Stopped")
    if gv.status_label is not None:
        gv.status_label.configure(text=gv.status_message)
    button.configure(text="Start Stash", command=partial(start_stash, button))
