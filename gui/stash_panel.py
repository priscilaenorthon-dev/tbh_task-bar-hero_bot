from functools import partial
from tkinter import BooleanVar, Button, Canvas, Checkbutton, DISABLED, Entry, Frame, IntVar, Label, Scrollbar, StringVar, Text, ttk

import utils.global_variables as gv
from gui.gui_functions import open_logs_folder, open_set_region_drag, pause_stash, popup_rectangle_window, run_diagnostics, start_map_runner, start_stash
from utils.config import WINDOW_SCALES, dict
from utils.map_data import ACT1, ACT2, ACT3, map_label

_HELP_FONT = ("Segoe UI", 8)
_SECTION_FONT = ("Segoe UI", 10, "bold")
_LABEL_FONT = ("Segoe UI", 9)

_BTN_START_BG = "#2da44e"
_BTN_START_ACTIVE = "#218838"
_BTN_STOP_BG = "#cf222e"
_BTN_STOP_ACTIVE = "#b91c1c"


def stash_panel():
    outer = Frame(gv.root, padx=8, pady=8)
    outer.pack(fill="both", expand=True)

    notebook = ttk.Notebook(outer)
    notebook.pack(fill="both", expand=True)

    _screen_tab(notebook)
    _timing_tab(notebook)
    _control_tab(notebook)
    _map_runner_tab(notebook)

    footer = Frame(outer)
    footer.pack(fill="x", side="bottom", pady=(8, 0))

    gv.status_label = Label(
        footer,
        text=gv.status_message,
        wraplength=640,
        justify="left",
        font=_LABEL_FONT,
    )
    gv.status_label.pack(fill="x", pady=(0, 4))
    gv.mr_status_label = gv.status_label

    # Stash start/stop + pause row
    stash_row = Frame(footer)
    stash_row.pack(fill="x", pady=(0, 4))

    stash_btn = Button(
        stash_row,
        text="Iniciar Stash",
        font=("Segoe UI", 10, "bold"),
        bg=_BTN_START_BG,
        fg="white",
        activebackground=_BTN_START_ACTIVE,
        activeforeground="white",
        relief="flat",
        pady=6,
    )
    stash_btn.configure(command=partial(start_stash, stash_btn))
    stash_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

    pause_btn = Button(
        stash_row,
        text="Pausar",
        font=("Segoe UI", 9),
        relief="flat",
        pady=6,
        width=10,
    )
    pause_btn.configure(command=partial(pause_stash, pause_btn))
    pause_btn.pack(side="right")

    # Map Runner button
    mr_button = Button(
        footer,
        text="Iniciar Caça ao Baú",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        pady=6,
    )
    mr_button.configure(command=partial(start_map_runner, mr_button, stash_btn))
    mr_button.pack(fill="x")


def _scrollable_tab(notebook, title):
    tab = Frame(notebook)
    notebook.add(tab, text=title)

    canvas = Canvas(tab, highlightthickness=0)
    scrollbar = Scrollbar(tab, orient="vertical", command=canvas.yview)
    inner = Frame(canvas, padx=6, pady=4)

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return inner


def _screen_tab(notebook):
    panel = _scrollable_tab(notebook, "Tela")
    row = 0

    row = _section(panel, row, "Região de busca")
    row = _help(
        panel,
        row,
        "Retângulo da tela onde o bot procura botões e ícones de baú. "
        "Use Desenhar para definir; Visualizar mostra a região atual. Áreas menores são mais rápidas.",
    )

    region = dict["search_region"]
    draw_button = Button(panel, text="Desenhar região de busca")
    draw_button.configure(
        command=partial(
            open_set_region_drag,
            region["x"],
            region["y"],
            region["width"],
            region["height"],
        )
    )
    draw_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 4))
    row += 1

    preview_button = Button(panel, text="Visualizar região")
    preview_button.configure(
        command=partial(
            popup_rectangle_window,
            preview_button,
            region["x"],
            region["y"],
            region["width"],
            region["height"],
        )
    )
    preview_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    row += 1
    row = _help(
        panel,
        row,
        "Desenhar: sobreposição escurecida em tela cheia — clique esquerdo e arraste "
        "(veja o console para logs de Desenho de região:). "
        "Configure o nível de log para DEBUG na aba Executar para coordenadas de arrastar. "
        "Visualizar: clique uma vez para fechar.",
    )

    row = _section(panel, row, "Escala da janela do jogo")
    Label(panel, text="Escala de UI", font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    scale_combo = ttk.Combobox(
        panel,
        textvariable=dict["window_scale"],
        values=WINDOW_SCALES,
        state="readonly",
        width=8,
    )
    scale_combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
    row += 1
    row = _help(
        panel,
        row,
        "Corresponda à escala da janela do TBH no jogo. As imagens dos botões carregam com sufixo: "
        "1 = sem sufixo (auto_fill.png), 1.25 = _1-25, 1.5 = _1-50, 2 = _2.",
    )

    row = _section(panel, row, "Comparação de templates")
    row = _range_row(
        panel,
        row,
        "Limiar de correspondência",
        dict["matching"]["threshold"],
        dict["matching"]["threshold"],
        is_single=True,
        suffix="",
    )
    row = _help(
        panel,
        row,
        "O quão próximo um screenshot deve corresponder a um template (0–1). "
        "Menor = mais permissivo, mais falsos positivos. "
        "Alterações aplicadas na próxima busca enquanto o bot estiver rodando.",
    )


def _timing_tab(notebook):
    panel = _scrollable_tab(notebook, "Temporização")
    row = 0

    row = _section(panel, row, "Atrasos de sondagem (aguardando UI)")
    row = _seconds_range_row(panel, row, "Repetição do loop", dict["timeouts"]["loop"])
    row = _help(
        panel,
        row,
        "Quando um botão ou ícone de baú não é encontrado, o bot aguarda um tempo aleatório "
        "neste intervalo (segundos) antes de buscar novamente. Intervalos mais amplos parecem menos robóticos.",
    )
    row = _seconds_range_row(panel, row, "Limite de espera da etapa", dict["timeouts"]["step_wait"])
    row = _help(
        panel,
        row,
        "Enquanto aguarda um ícone de baú ou botão de etapa do stash, o assistente desiste após um tempo "
        "aleatório neste intervalo (segundos) e pula para a próxima etapa. Evita ficar preso indefinidamente.",
    )

    row = _section(panel, row, "Após cliques bem-sucedidos")
    row = _seconds_range_row(panel, row, "Pausa após clique", dict["timeouts"]["after_click"])
    row = _help(
        panel,
        row,
        "Pausa aleatória (segundos) após etapas de stash, abrir um baú ou finalizar combine. "
        "Dá tempo para a UI do jogo animar antes da próxima ação.",
    )

    row = _section(panel, row, "Auto Fill → Verificação de combine")
    row = _seconds_range_row(panel, row, "Espera antes do combine", dict["combine_flow"]["wait"])
    row = _help(
        panel,
        row,
        "Após clicar em Auto Fill, o bot aguarda um tempo aleatório neste intervalo (segundos), "
        "depois procura o prompt de combine. Muito curto pode perder o prompt; muito longo atrasa o loop.",
    )

    row = _section(panel, row, "Stash / sort em segundo plano")
    row = _seconds_range_row(
        panel, row, "Intervalo do ciclo", dict["periodic_stash_sort"]["interval"]
    )
    row = _help(
        panel,
        row,
        "Durante a execução, o bot tenta periodicamente Stash All + Sort e pressiona Espaço. "
        "Cada ciclo é agendado após um atraso aleatório neste intervalo (segundos).",
    )
    row = _seconds_range_row(
        panel, row, "Intervalo Stash → Sort", dict["periodic_stash_sort"]["between_clicks"]
    )
    row = _help(
        panel,
        row,
        "Atraso aleatório (segundos) entre o clique periódico em Stash All e o clique em Sort quando ambos são encontrados.",
    )

    row = _section(panel, row, "Variação de posição do clique")
    row = _int_range_row(
        panel, row, "Deslocamento em pixels", dict["randomization"]["click_offset_px"]
    )
    row = _help(
        panel,
        row,
        "Cada clique adiciona um deslocamento X/Y aleatório neste intervalo (pixels) a partir do centro do template. "
        "Evita cliques idênticos no mesmo pixel. Use mín negativo (ex.: -8) e máx positivo (ex.: 8).",
    )


def _control_tab(notebook):
    panel = _scrollable_tab(notebook, "Executar")
    row = 0

    # Log level
    row = _section(panel, row, "Registro de log")
    log_values = ("DEBUG", "INFO", "WARNING", "ERROR")
    Label(panel, text="Nível de log", font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    log_combo = ttk.Combobox(
        panel,
        textvariable=dict["log_lvl"],
        values=log_values,
        state="readonly",
        width=12,
    )
    log_combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
    row += 1
    row = _help(
        panel,
        row,
        "Detalhe do console enquanto o bot roda. DEBUG mostra o score de cada template; INFO é recomendado. "
        "Aplicado quando você clica em Iniciar Stash.",
    )

    # Chest counters
    row = _section(panel, row, "Contadores de baús (sessão atual)")
    counter_frame = Frame(panel)
    counter_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))

    Label(counter_frame, text="Marrom:", font=_LABEL_FONT).pack(side="left")
    gv.lbl_chest_count = Label(
        counter_frame, text="0", font=("Segoe UI", 11, "bold"), fg="#8B4513"
    )
    gv.lbl_chest_count.pack(side="left", padx=(4, 16))

    Label(counter_frame, text="Boss (azul):", font=_LABEL_FONT).pack(side="left")
    gv.lbl_boss_chest_count = Label(
        counter_frame, text="0", font=("Segoe UI", 11, "bold"), fg="#1565C0"
    )
    gv.lbl_boss_chest_count.pack(side="left", padx=(4, 16))

    Label(counter_frame, text="Total:", font=_LABEL_FONT).pack(side="left")
    gv.lbl_total_count = Label(
        counter_frame, text="0", font=("Segoe UI", 11, "bold")
    )
    gv.lbl_total_count.pack(side="left", padx=(4, 0))
    row += 1

    # Activity log
    row = _section(panel, row, "Atividade recente")
    act_frame = Frame(panel)
    act_frame.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(0, 4))
    act_scroll = Scrollbar(act_frame, orient="vertical")
    act_text = Text(
        act_frame,
        height=6,
        width=60,
        font=("Consolas", 8),
        yscrollcommand=act_scroll.set,
        state=DISABLED,
        wrap="word",
        bg="#f5f5f5",
        relief="flat",
        borderwidth=1,
    )
    act_scroll.config(command=act_text.yview)
    act_text.pack(side="left", fill="both", expand=True)
    act_scroll.pack(side="right", fill="y")
    gv.activity_log_widget = act_text
    row += 1

    # Log file path + open folder button
    log_path_frame = Frame(panel)
    log_path_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    gv.lbl_log_path = Label(
        log_path_frame,
        text="Log: (não iniciado)",
        font=_HELP_FONT,
        fg="#555555",
        anchor="w",
    )
    gv.lbl_log_path.pack(side="left", fill="x", expand=True)
    Button(
        log_path_frame,
        text="Abrir pasta de logs",
        font=_HELP_FONT,
        command=open_logs_folder,
        relief="flat",
    ).pack(side="right")
    row += 1

    # Diagnostics
    row = _section(panel, row, "Diagnóstico")
    diag_frame = Frame(panel)
    diag_frame.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(4, 4))
    diag_scroll = Scrollbar(diag_frame, orient="vertical")
    diag_text = Text(
        diag_frame,
        height=9,
        width=60,
        font=("Consolas", 9),
        yscrollcommand=diag_scroll.set,
        state=DISABLED,
        wrap="word",
    )
    diag_scroll.config(command=diag_text.yview)
    diag_text.pack(side="left", fill="both", expand=True)
    diag_scroll.pack(side="right", fill="y")
    row += 1

    diag_button = Button(panel, text="Executar diagnóstico")
    diag_button.configure(command=partial(run_diagnostics, diag_button, diag_text))
    diag_button.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4))
    row += 1

    row = _help(
        panel,
        row,
        "Verifica região de busca, captura de tela, arquivos de template e scores do buscador de imagem "
        "para cada template configurado. AVISO significa que a busca rodou mas nada foi encontrado "
        "(coloque a UI do jogo na região). Nenhum clique é realizado.",
    )


def _map_runner_tab(notebook):
    _DIFFICULTIES = ("normal", "nightmare", "hell", "torment")

    panel = _scrollable_tab(notebook, "Caça ao Baú")
    row = 0

    row = _section(panel, row, "Baús a coletar")
    Checkbutton(
        panel, text="Baú marrom (chest)", variable=dict["map_runner"]["click_chest"], font=_LABEL_FONT
    ).grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1
    Checkbutton(
        panel, text="Baú azul chefe (boss chest)", variable=dict["map_runner"]["click_boss_chest"], font=_LABEL_FONT
    ).grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1
    Checkbutton(
        panel,
        text="Fazer Auto Fill + Stash após abrir baú azul",
        variable=dict["map_runner"]["do_stash_after_chest"],
        font=_LABEL_FONT,
    ).grid(row=row, column=0, columnspan=2, sticky="w", padx=(20, 0))
    row += 1
    row = _help(
        panel,
        row,
        "Marcado: após encontrar o baú azul, faz Auto Fill e Stash antes de ir ao próximo mapa. "
        "Desmarcado: apenas coleta o baú e avança para o próximo mapa.",
    )

    row = _section(panel, row, "Mapas e dificuldade por mapa")
    row = _help(
        panel,
        row,
        "Selecione os mapas da rota e a dificuldade de cada um individualmente. "
        "O bot visitará os mapas marcados em ordem repetida.",
    )

    acts_frame = Frame(panel)
    acts_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 8))
    row += 1

    for col, (act_label, act_codes) in enumerate([("Act 1", ACT1), ("Act 2", ACT2), ("Act 3", ACT3)]):
        col_frame = Frame(acts_frame, padx=8)
        col_frame.grid(row=0, column=col, sticky="nw")
        Label(col_frame, text=act_label, font=_SECTION_FONT).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        for map_row, code in enumerate(act_codes, start=1):
            map_var = dict["map_runner"]["selected_maps"][code]
            diff_var = dict["map_runner"]["map_difficulties"][code]
            Checkbutton(
                col_frame, text=map_label(code), variable=map_var, font=_LABEL_FONT, anchor="w"
            ).grid(row=map_row, column=0, sticky="w")
            ttk.Combobox(
                col_frame,
                textvariable=diff_var,
                values=_DIFFICULTIES,
                state="readonly",
                width=9,
            ).grid(row=map_row, column=1, sticky="w", padx=(6, 0))

    row = _section(panel, row, "Temporizador de respawn")
    Label(panel, text="Respawn do baú (min)", font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    Entry(panel, textvariable=dict["map_runner"]["chest_respawn_minutes"], width=8).grid(
        row=row, column=1, sticky="w", padx=(8, 0)
    )
    row += 1
    row = _help(panel, row, "Minutos para o baú reaparecer (mesmo valor para todos os mapas).")

    row = _section(panel, row, "Tempo por mapa")
    row = _seconds_range_row(panel, row, "Duração por mapa", dict["map_runner"]["time_per_map"])
    row = _help(panel, row, "Tempo aleatório (segundos) coletando em cada mapa antes de avançar.")

    row = _section(panel, row, "Velocidade de navegação")
    row = _seconds_range_row(panel, row, "Delay entre cliques", dict["map_runner"]["nav_click_delay"])
    row = _help(panel, row, "Pausa entre cada clique de navegação (dropdown → dificuldade → Act → nó do mapa).")


def _section(parent, row, title):
    Label(parent, text=title, font=_SECTION_FONT).grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(10, 4)
    )
    return row + 1


def _help(parent, row, text):
    Label(
        parent,
        text=text,
        font=_HELP_FONT,
        fg="#555555",
        wraplength=600,
        justify="left",
    ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))
    return row + 1


def _seconds_range_row(parent, row, label, range_dict):
    return _range_row(
        parent,
        row,
        label,
        range_dict["min"],
        range_dict["max"],
        suffix=" s",
    )


def _int_range_row(parent, row, label, range_dict):
    return _range_row(
        parent,
        row,
        label,
        range_dict["min"],
        range_dict["max"],
        suffix=" px",
    )


def _range_row(parent, row, label, min_var, max_var, is_single=False, suffix=""):
    Label(parent, text=label, font=_LABEL_FONT).grid(row=row, column=0, sticky="w")
    frame = Frame(parent)
    frame.grid(row=row, column=1, sticky="w", padx=(8, 0))

    if is_single:
        Entry(frame, textvariable=min_var, width=8).pack(side="left")
    else:
        Label(frame, text="mín", font=_HELP_FONT).pack(side="left")
        Entry(frame, textvariable=min_var, width=7).pack(side="left", padx=(4, 8))
        Label(frame, text="máx", font=_HELP_FONT).pack(side="left")
        Entry(frame, textvariable=max_var, width=7).pack(side="left", padx=(4, 0))

    if suffix:
        Label(frame, text=suffix.strip(), font=_HELP_FONT).pack(side="left", padx=(6, 0))
    return row + 1
