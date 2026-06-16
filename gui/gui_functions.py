from functools import partial
from tkinter import Canvas, Frame, Label, Toplevel, DISABLED, END, NORMAL

import utils.global_variables as gv
from functionality.function_tester import run_diagnostics as execute_diagnostics
from functionality.stash_loop import reset_stash_state, start_periodic_stash_sort, stash_loop
from utils.config import dict as cfg, save_data
from wrappers.logging_wrapper import apply_log_level, debug, enable_file_logging, info, warning

_MIN_REGION_SIZE = 20
_OVERLAY_ALPHA = 0.25


def popup_rectangle_window(button, x, y, width, height):
    """Exibe a região atual; clique em qualquer lugar para fechar."""
    apply_log_level()
    info("Prévia da região: abrindo sobreposição")
    window, canvas, bar = _create_overlay()
    window.update_idletasks()
    info(
        "Prévia da região: canvas na tela "
        f"({canvas.winfo_rootx()}, {canvas.winfo_rooty()}) "
        f"tamanho {canvas.winfo_width()}x{canvas.winfo_height()}"
    )
    _draw_region_on_canvas(canvas, x.get(), y.get(), width.get(), height.get())

    def close(_event=None):
        if _event is not None:
            debug(f"Prévia da região: fechar em ({_event.x_root}, {_event.y_root})")
        info("Prévia da região: fechada")
        window.destroy()
        button.configure(
            command=partial(popup_rectangle_window, button, x, y, width, height)
        )

    _bind_click_close(window, canvas, bar, close)
    button.configure(command=partial(close))


def open_set_region_drag(x, y, width, height):
    """Sobreposição em tela cheia: arraste com esquerdo para definir região de busca (coordenadas de tela)."""
    apply_log_level()
    info("Desenho de região: abrindo sobreposição (escurecida, captura o mouse)")
    window, canvas, bar = _create_overlay()
    window.update_idletasks()
    debug(
        "Desenho de região: canvas na tela "
        f"({canvas.winfo_rootx()}, {canvas.winfo_rooty()}) "
        f"tamanho {canvas.winfo_width()}x{canvas.winfo_height()}"
    )
    drag = {"rect_id": None, "start_x": None, "start_y": None}

    if width.get() >= _MIN_REGION_SIZE and height.get() >= _MIN_REGION_SIZE:
        drag["rect_id"] = _draw_region_on_canvas(
            canvas, x.get(), y.get(), width.get(), height.get(), outline="#88ff88"
        )
        debug(
            f"Desenho de região: exibindo região atual "
            f"({x.get()}, {y.get()}) {width.get()}x{height.get()}"
        )
    else:
        debug("Desenho de região: nenhuma região atual — arraste um novo retângulo")

    def close(_event=None):
        if _event is not None:
            debug(f"Desenho de região: cancelar em ({_event.x_root}, {_event.y_root})")
        info("Desenho de região: sobreposição fechada")
        window.destroy()

    def on_press(event):
        drag["start_x"] = event.x_root
        drag["start_y"] = event.y_root
        debug(f"Desenho de região: pressionado na tela ({event.x_root}, {event.y_root})")
        if drag["rect_id"] is not None:
            canvas.delete(drag["rect_id"])
            drag["rect_id"] = None
        cx1, cy1 = _screen_to_canvas(canvas, event.x_root, event.y_root)
        debug(f"Desenho de região: pressionado no canvas ({cx1:.0f}, {cy1:.0f})")
        drag["rect_id"] = canvas.create_rectangle(
            cx1, cy1, cx1, cy1, outline="lime", width=3
        )

    def on_motion(event):
        if drag["rect_id"] is None or drag["start_x"] is None:
            return
        cx1, cy1 = _screen_to_canvas(canvas, drag["start_x"], drag["start_y"])
        cx2, cy2 = _screen_to_canvas(canvas, event.x_root, event.y_root)
        canvas.coords(drag["rect_id"], cx1, cy1, cx2, cy2)
        debug(f"Desenho de região: arrastando para tela ({event.x_root}, {event.y_root})")

    def on_release(event):
        if drag["start_x"] is None:
            warning("Desenho de região: solto sem pressionar — ignorado")
            return
        left = min(drag["start_x"], event.x_root)
        top = min(drag["start_y"], event.y_root)
        region_width = abs(event.x_root - drag["start_x"])
        region_height = abs(event.y_root - drag["start_y"])
        debug(
            f"Desenho de região: solto em ({event.x_root}, {event.y_root}) "
            f"→ {region_width}x{region_height} px"
        )
        if region_width < _MIN_REGION_SIZE or region_height < _MIN_REGION_SIZE:
            warning(
                f"Desenho de região: muito pequeno ({region_width}x{region_height}), "
                f"mínimo {_MIN_REGION_SIZE}px — tente novamente"
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
        debug(f"Desenho de região: aplicado ({left}, {top}) {region_width}x{region_height}")
        close()

    _bind_drag(window, canvas, bar, on_press, on_motion, on_release)
    window.bind("<Escape>", close)
    info("Desenho de região: pronto — clique esquerdo e arraste na tela escurecida (Esc para cancelar)")


def _create_overlay():
    """
    Sobreposição semitransparente em tela cheia.

    Evita -transparentcolor, que no Windows deixa os cliques passarem para o
    jogo/desktop, impedindo o arrastar.
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
        text="Arraste com clique esquerdo para definir região de busca  •  Esc para cancelar",
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
        f"Sobreposição de região: retângulo canvas ({cx1:.0f},{cy1:.0f})-({cx2:.0f},{cy2:.0f})"
    )
    return canvas.create_rectangle(cx1, cy1, cx2, cy2, outline=outline, width=3)


def on_closing():
    save_data()
    info("GUI: Salvando dados")
    info("GUI: Fechando")
    gv.root.destroy()


def start_stash(button):
    apply_log_level()
    gv.continue_stash = True
    reset_stash_state()
    button.configure(text="Parar Stash", command=partial(stop_stash, button))
    stash_loop()
    start_periodic_stash_sort()


_STATUS_COLORS = {
    "PASS": "#1a7f37",
    "WARN": "#9a6700",
    "FAIL": "#cf222e",
}

_STATUS_LABELS = {
    "PASS": "OK",
    "WARN": "AVISO",
    "FAIL": "FALHA",
}


def run_diagnostics(button, output_text):
    apply_log_level()
    button.configure(state=DISABLED)
    output_text.configure(state=NORMAL)
    output_text.delete("1.0", END)
    output_text.insert(END, "Executando diagnóstico...\n")
    output_text.configure(state=DISABLED)
    gv.root.update_idletasks()

    try:
        results = execute_diagnostics()
    except Exception as exc:
        results = [("Diagnóstico", "FAIL", str(exc))]

    lines = []
    for name, status, detail in results:
        label = _STATUS_LABELS.get(status, status)
        lines.append(f"[{label}] {name}: {detail}")

    passed = sum(1 for _, status, _ in results if status == "PASS")
    warned = sum(1 for _, status, _ in results if status == "WARN")
    failed = sum(1 for _, status, _ in results if status == "FAIL")
    lines.append("")
    lines.append(f"Resumo: {passed} ok, {warned} aviso, {failed} falha")

    output_text.configure(state=NORMAL)
    output_text.delete("1.0", END)
    for line in lines:
        if line.startswith("[OK]"):
            tag = "pass"
        elif line.startswith("[AVISO]"):
            tag = "warn"
        elif line.startswith("[FALHA]"):
            tag = "fail"
        else:
            tag = None
        if tag:
            output_text.insert(END, line + "\n", tag)
        else:
            output_text.insert(END, line + "\n")
    output_text.tag_config("pass", foreground=_STATUS_COLORS["PASS"])
    output_text.tag_config("warn", foreground=_STATUS_COLORS["WARN"])
    output_text.tag_config("fail", foreground=_STATUS_COLORS["FAIL"])
    output_text.configure(state=DISABLED)
    button.configure(state=NORMAL)

    summary = f"Diagnóstico: {passed} ok, {warned} aviso, {failed} falha"
    gv.status_message = summary
    if gv.status_label is not None:
        gv.status_label.configure(text=summary)
    info(summary)


def stop_stash(button):
    gv.continue_stash = False
    gv.status_message = "Parado"
    info("Processo parado")
    if gv.status_label is not None:
        gv.status_label.configure(text=gv.status_message)
    button.configure(text="Iniciar Stash", command=partial(start_stash, button))


def start_map_runner(mr_button, stash_button):
    from functionality.map_runner_loop import map_runner_loop, reset_map_runner_state

    apply_log_level()
    active_maps = [code for code, var in cfg["map_runner"]["selected_maps"].items() if var.get()]
    if not active_maps:
        warning("Map Runner: selecione pelo menos um mapa antes de iniciar")
        gv.mr_status_message = "Erro: nenhum mapa selecionado"
        if gv.mr_status_label is not None:
            gv.mr_status_label.configure(text=gv.mr_status_message)
        return

    gv.continue_map_runner = True
    reset_map_runner_state()

    log_path = enable_file_logging()
    info(f"Map Runner: log em arquivo → {log_path}")

    if stash_button is not None:
        stash_button.configure(state=DISABLED)
    mr_button.configure(
        text="Parar Caça ao Baú",
        command=partial(stop_map_runner, mr_button, stash_button),
    )
    info("Map Runner: iniciado")
    map_runner_loop()


def stop_map_runner(mr_button, stash_button):
    gv.continue_map_runner = False
    gv.continue_stash = False
    gv.mr_status_message = "Parado"
    info("Map Runner: parado")
    if gv.mr_status_label is not None:
        gv.mr_status_label.configure(text=gv.mr_status_message)
    if stash_button is not None:
        stash_button.configure(state=NORMAL)
    mr_button.configure(
        text="Iniciar Caça ao Baú",
        command=partial(start_map_runner, mr_button, stash_button),
    )
