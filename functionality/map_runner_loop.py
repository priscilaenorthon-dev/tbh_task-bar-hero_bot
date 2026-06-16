import random
import time
from pathlib import Path

import utils.global_variables as gv
from functionality.image_search import find_template
from functionality.stash_loop import reset_stash_state, start_periodic_stash_sort, stash_loop
from utils.config import dict as cfg, random_click_offset, random_delay_ms, random_timeout, template_path_for
from utils.map_data import act_of, map_label, template_for
from wrappers.logging_wrapper import debug, info, warning
from wrappers.win32api_wrapper import click_mouse_with_coordinates, right_click_mouse_with_coordinates, scroll_at

_ACT_KEYS = {"1": "act1", "2": "act2", "3": "act3"}
_MAX_SCROLL_ATTEMPTS = 14
_SCROLL_DOWN = -120
_SCROLL_UP   =  120
# Stages com número ≤ 5 ficam no terço inferior do mapa (scroll down),
# stages ≥ 6 ficam no terço superior (scroll up).
_SCROLL_BOTTOM_STAGES = {1, 2, 3, 4, 5}
# Tempo máximo (ms) aguardando o ciclo de stash após clicar no baú azul
_STASH_AFTER_CHEST_MS = 18_000


def _scroll_delta_for(code: str) -> int:
    """Retorna o delta de scroll adequado para alcançar o nó no mapa do portal."""
    stage = int(code.split("-")[1])
    return _SCROLL_DOWN if stage in _SCROLL_BOTTOM_STAGES else _SCROLL_UP


def _active_map_codes():
    """Retorna lista ordenada de códigos de mapa com checkbox marcado."""
    return [
        code
        for code, var in cfg["map_runner"]["selected_maps"].items()
        if var.get()
    ]


def reset_map_runner_state():
    gv.mr_current_map_index = 0
    gv.mr_map_last_collected = {}
    gv.mr_stash_phase_deadline = None
    gv.mr_status_message = "Iniciando..."
    _update_mr_status()


def map_runner_loop():
    if not gv.continue_map_runner:
        gv.mr_status_message = "Parado"
        _update_mr_status()
        return
    _navigate_phase()


# ── NAVIGATE ─────────────────────────────────────────────────────────────────

def _navigate_phase():
    maps = _active_map_codes()
    if not maps:
        warning("Map Runner: nenhum mapa selecionado")
        gv.mr_status_message = "Erro: nenhum mapa selecionado"
        _update_mr_status()
        return

    target_idx = gv.mr_current_map_index % len(maps)
    code = maps[target_idx]
    label = map_label(code)

    info(f"Map Runner: navegando para '{label}'")
    gv.mr_status_message = f"Navegando para {label}..."
    _update_mr_status()

    _click_difficulty_dropdown(code)


def _click_difficulty_dropdown(code, phase=0, attempt=0):
    """Seleciona a dificuldade correta no portal (por mapa).

    Fase 0: verifica se a dificuldade já está correta (botão fechado visível).
    Fase 1: dropdown foi aberto — procura a opção alvo para clicar.
    """
    if not gv.continue_map_runner:
        return

    # Lê a dificuldade específica deste mapa
    diff_var = cfg["map_runner"]["map_difficulties"].get(code)
    difficulty = diff_var.get().lower() if diff_var is not None else "normal"
    template_key = difficulty if difficulty in ("normal", "nightmare", "hell", "torment") else "normal"
    _MAX_ATTEMPTS = 8

    def _proceed():
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                      lambda: _click_act_tab(code))

    diff_region = _header_region(220)
    open_region = _header_region(420)
    threshold = cfg["matching"]["threshold"].get()
    diff_threshold = max(0.82, threshold)

    # ── Fase 0: verificar se já está na dificuldade correta ──────────────────
    if phase == 0:
        try:
            path = _nav_template_path(template_key)
            match = find_template(diff_region, path, diff_threshold)
            if match is not None:
                debug(f"Map Runner: dificuldade '{difficulty}' já selecionada (score={match[2]:.3f})")
                _proceed()
                return
        except FileNotFoundError:
            debug(f"Map Runner: template '{template_key}' não encontrado — pulando verificação")
            _proceed()
            return

        _DIFF_KEYS = ("normal", "nightmare", "hell", "torment", "difficulty_dropdown")
        _FIND_THRESHOLD = 0.65
        best_match = None
        best_score = 0.0
        for _key in _DIFF_KEYS:
            try:
                _path = _nav_template_path(_key)
                _m = find_template(diff_region, _path, _FIND_THRESHOLD)
                if _m is not None and _m[2] > best_score:
                    best_match = _m
                    best_score = _m[2]
            except FileNotFoundError:
                continue

        if best_match is None:
            debug("Map Runner: botão de dificuldade não encontrado, aguardando...")
            gv.root.after(random_delay_ms(cfg["timeouts"]["loop"]),
                          lambda: _click_difficulty_dropdown(code, phase=0))
            return

        cx, cy, _ = best_match
        ox, oy = random_click_offset()
        click_mouse_with_coordinates(cx + ox, cy + oy)
        info(f"Map Runner: dropdown de dificuldade aberto em ({cx},{cy}) score={best_score:.3f}")
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                      lambda: _click_difficulty_dropdown(code, phase=1, attempt=0))
        return

    # ── Fase 1: dropdown aberto — procura a opção alvo ───────────────────────
    if attempt == 0:
        _save_debug_screenshot("dropdown_open")

    open_key = f"{template_key}_open"
    try:
        path = _nav_template_path(open_key)
        match = find_template(open_region, path, threshold)
        if match is not None:
            cx, cy, score = match
            ox, oy = random_click_offset()
            click_mouse_with_coordinates(cx + ox, cy + oy)
            info(f"Map Runner: dificuldade '{difficulty}' clicada (aberto) em ({cx},{cy}) score={score:.3f}")
            gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                          lambda: _click_difficulty_dropdown(code, phase=0))
            return
    except FileNotFoundError:
        debug(f"Map Runner: template '{open_key}' não encontrado")

    if attempt >= _MAX_ATTEMPTS:
        warning(f"Map Runner: opção '{difficulty}' não encontrada no seletor — continuando assim mesmo")
        _proceed()
        return

    debug(f"Map Runner: aguardando opção '{difficulty}' no seletor (tentativa {attempt+1}/{_MAX_ATTEMPTS})...")
    gv.root.after(random_delay_ms(cfg["timeouts"]["loop"]),
                  lambda: _click_difficulty_dropdown(code, phase=1, attempt=attempt + 1))


_ACT_TAB_SPACING = 140
_MAX_TAB_ATTEMPTS = 6


def _click_act_tab(code, attempt=0):
    """Navega para a aba do Act correto."""
    if not gv.continue_map_runner:
        return

    act = act_of(code)
    target_num = int(act)
    tab_region = _header_region(300)
    threshold = min(0.55, cfg["matching"]["threshold"].get())

    def _go_to_node():
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                      lambda: _find_map_node(code, scroll_attempts=0))

    if attempt == 0:
        _save_debug_screenshot("act_tab_region")

    best_act  = None
    best_m    = None
    best_score = 0.0
    for _act_key, _act_id in [("act1","1"), ("act2","2"), ("act3","3")]:
        try:
            _path = _nav_template_path(_act_key)
            _m = find_template(tab_region, _path, threshold)
            if _m is not None and _m[2] > best_score:
                best_score = _m[2]
                best_m     = _m
                best_act   = _act_id
        except FileNotFoundError:
            continue

    if best_act is None:
        if attempt >= _MAX_TAB_ATTEMPTS:
            info(f"Map Runner: aba Act {act} não localizada após {attempt} tentativas — continuando")
            _go_to_node()
            return
        debug(f"Map Runner: nenhuma aba Act encontrada, tentativa {attempt + 1}/{_MAX_TAB_ATTEMPTS}...")
        gv.root.after(random_delay_ms(cfg["timeouts"]["loop"]),
                      lambda: _click_act_tab(code, attempt + 1))
        return

    if best_act == act:
        debug(f"Map Runner: Act {act} já ativo (score={best_score:.3f}) → indo para nó")
        _go_to_node()
        return

    if attempt >= _MAX_TAB_ATTEMPTS:
        warning(f"Map Runner: Act {act} não confirmado após {attempt} tentativas — continuando")
        _go_to_node()
        return

    ax, ay, _ = best_m
    offset = (target_num - int(best_act)) * _ACT_TAB_SPACING
    tx = ax + offset
    ox, oy = random_click_offset()
    click_mouse_with_coordinates(tx + ox, ay + oy)
    info(f"Map Runner: clicou Act {act} em ({tx},{ay}) via offset de Act {best_act} score={best_score:.3f}")
    gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                  lambda: _click_act_tab(code, attempt + 1))


def _find_map_node(code, scroll_attempts):
    if not gv.continue_map_runner:
        return

    label = map_label(code)
    asset_path = template_for(code)

    from tkinter import StringVar as _SV
    _proxy = _SV(value=Path(asset_path).name)

    try:
        path = template_path_for(_proxy)
    except FileNotFoundError:
        warning(f"Map Runner: template do mapa '{label}' não encontrado em assets/")
        gv.mr_status_message = f"Erro: template de '{label}' não encontrado"
        _update_mr_status()
        _advance_to_next_map()
        return

    region = _search_region()
    threshold = cfg["matching"]["threshold"].get()
    match = find_template(region, path, threshold)

    if match is not None:
        cx, cy, score = match
        ox, oy = random_click_offset()
        click_mouse_with_coordinates(cx + ox, cy + oy)
        info(f"Map Runner: nó '{label}' clicado em ({cx},{cy}) score={score:.3f}")
        # Após clicar no mapa, inicia a caça ao baú azul
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]), _start_chest_hunt)
        return

    if scroll_attempts >= _MAX_SCROLL_ATTEMPTS:
        warning(f"Map Runner: nó '{label}' não encontrado após {_MAX_SCROLL_ATTEMPTS} scrolls — pulando")
        gv.mr_status_message = f"Mapa '{label}' não encontrado"
        _update_mr_status()
        _advance_to_next_map()
        return

    rx = cfg["search_region"]["x"].get() + cfg["search_region"]["width"].get() // 2
    ry = cfg["search_region"]["y"].get() + cfg["search_region"]["height"].get() // 2
    delta = _scroll_delta_for(code)
    scroll_at(rx, ry, delta)
    direction = "baixo" if delta < 0 else "cima"
    debug(f"Map Runner: scroll {direction} {scroll_attempts + 1}/{_MAX_SCROLL_ATTEMPTS} procurando '{label}'")

    gv.root.after(
        random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
        lambda: _find_map_node(code, scroll_attempts + 1),
    )


# ── BOSS CHEST HUNT ───────────────────────────────────────────────────────────

def _start_chest_hunt():
    """Após navegar para o mapa, aguarda o ícone do baú azul aparecer."""
    if not gv.continue_map_runner:
        return

    maps = _active_map_codes()
    current_idx = gv.mr_current_map_index % len(maps)
    label = map_label(maps[current_idx])

    gv.mr_status_message = f"Procurando baú azul em {label}..."
    _update_mr_status()
    _hunt_for_boss_chest()


def _hunt_for_boss_chest():
    """Varre a região de busca pelo ícone de baú azul (boss chest). Clica quando encontra."""
    if not gv.continue_map_runner:
        return

    region = _search_region()
    threshold = cfg["matching"]["threshold"].get()
    boss_path = _boss_chest_template_path()

    if boss_path is None:
        warning("Map Runner: template de baú azul não configurado, avançando")
        _record_and_advance()
        return

    match = find_template(region, boss_path, threshold)
    if match is None:
        debug("Map Runner: baú azul não encontrado, aguardando...")
        gv.root.after(random_delay_ms(cfg["timeouts"]["loop"]), _hunt_for_boss_chest)
        return

    cx, cy, score = match
    info(f"Map Runner: baú azul encontrado em ({cx},{cy}) score={score:.3f}")

    # Micro-pausa humana antes de clicar (30% de chance)
    delay_ms = random_delay_ms(cfg["timeouts"]["after_click"])
    if random.random() < 0.30:
        delay_ms += random.randint(150, 500)

    gv.root.after(delay_ms, lambda: _click_boss_chest_found(cx, cy))


def _click_boss_chest_found(cx, cy):
    """Clica com botão direito no baú azul e decide se faz stash."""
    if not gv.continue_map_runner:
        return

    ox, oy = random_click_offset()
    right_click_mouse_with_coordinates(cx + ox, cy + oy)

    maps = _active_map_codes()
    current_idx = gv.mr_current_map_index % len(maps)
    label = map_label(maps[current_idx])
    gv.mr_status_message = f"Baú azul aberto em {label}!"
    _update_mr_status()

    # Incrementa contador de baús azuis
    gv.session_boss_chest_count += 1
    _update_chest_counter_labels()

    do_stash = cfg["map_runner"]["do_stash_after_chest"].get()
    delay_ms = random_delay_ms(cfg["timeouts"]["after_click"])

    if do_stash:
        info("Map Runner: fazendo stash após baú azul")
        gv.root.after(delay_ms, _start_stash_phase)
    else:
        info("Map Runner: pulando stash, indo para próximo mapa")
        gv.root.after(delay_ms, _record_and_advance)


def _boss_chest_template_path():
    """Retorna o path absoluto do template boss_chest_icon, ou None."""
    try:
        from utils.config import chest_check_entries
        for entry in chest_check_entries():
            if entry["name"] == "boss_chest":
                return entry["template"]
    except Exception:
        pass
    return None


def _update_chest_counter_labels():
    """Atualiza os labels de contador de baús na GUI."""
    total = gv.session_chest_count + gv.session_boss_chest_count
    if gv.lbl_chest_count is not None:
        gv.lbl_chest_count.configure(text=str(gv.session_chest_count))
    if gv.lbl_boss_chest_count is not None:
        gv.lbl_boss_chest_count.configure(text=str(gv.session_boss_chest_count))
    if gv.lbl_total_count is not None:
        gv.lbl_total_count.configure(text=str(total))


# ── STASH (após baú azul) ─────────────────────────────────────────────────────

def _start_stash_phase():
    """Roda um ciclo de stash (auto_fill → stash_all → fechar) após o baú azul."""
    if not gv.continue_map_runner:
        return

    maps = _active_map_codes()
    current_idx = gv.mr_current_map_index % len(maps)
    label = map_label(maps[current_idx])

    gv.mr_stash_phase_deadline = time.monotonic() + _STASH_AFTER_CHEST_MS / 1000.0

    info(f"Map Runner: stash após baú em '{label}' (até {_STASH_AFTER_CHEST_MS // 1000}s)")
    gv.mr_status_message = f"Stash em {label}..."
    _update_mr_status()

    gv.continue_stash = True
    reset_stash_state()
    # Pula open_chest (já clicamos) — começa do auto_fill (índice 1)
    gv.current_step_index = 1
    stash_loop()
    start_periodic_stash_sort()

    gv.root.after(_STASH_AFTER_CHEST_MS, _check_stash_phase_done)


def _check_stash_phase_done():
    if not gv.continue_map_runner:
        gv.continue_stash = False
        return

    if time.monotonic() >= gv.mr_stash_phase_deadline:
        _record_and_advance()
    else:
        remaining_ms = int((gv.mr_stash_phase_deadline - time.monotonic()) * 1000)
        gv.root.after(max(500, remaining_ms), _check_stash_phase_done)


# ── RECORD / ADVANCE ──────────────────────────────────────────────────────────

def _record_and_advance():
    gv.continue_stash = False
    gv.mr_stash_phase_deadline = None

    maps = _active_map_codes()
    current_idx = gv.mr_current_map_index % len(maps)
    label = map_label(maps[current_idx])
    gv.mr_map_last_collected[current_idx] = time.monotonic()
    info(f"Map Runner: '{label}' coletado")

    gv.mr_current_map_index = (gv.mr_current_map_index + 1) % len(maps)
    gv.root.after(random_delay_ms(cfg["timeouts"]["after_click"]), _wait_or_navigate)


def _advance_to_next_map():
    """Avança para o próximo mapa sem registrar coleta (mapa não encontrado)."""
    maps = _active_map_codes()
    gv.mr_current_map_index = (gv.mr_current_map_index + 1) % len(maps)
    gv.root.after(random_delay_ms(cfg["timeouts"]["after_click"]), _wait_or_navigate)


# ── WAIT ──────────────────────────────────────────────────────────────────────

def _wait_or_navigate():
    if not gv.continue_map_runner:
        return

    maps = _active_map_codes()
    respawn_s = cfg["map_runner"]["chest_respawn_minutes"].get() * 60.0
    now = time.monotonic()

    for offset in range(len(maps)):
        idx = (gv.mr_current_map_index + offset) % len(maps)
        last = gv.mr_map_last_collected.get(idx)
        if last is None or (now - last) >= respawn_s:
            gv.mr_current_map_index = idx
            _navigate_phase()
            return

    soonest_idx = min(
        gv.mr_map_last_collected.keys(),
        key=lambda i: gv.mr_map_last_collected[i],
    )
    expires_at = gv.mr_map_last_collected[soonest_idx] + respawn_s
    wait_s = max(0.0, expires_at - now)
    label = map_label(maps[soonest_idx])
    info(f"Map Runner: aguardando {wait_s:.0f}s para '{label}'")
    gv.mr_status_message = f"Aguardando respawn... {int(wait_s)}s"
    _update_mr_status()

    check_ms = min(10_000, int(wait_s * 1000))
    gv.root.after(max(1_000, check_ms), _wait_or_navigate)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nav_template_path(key):
    var = cfg["map_runner"]["nav_templates"].get(key)
    if var is None:
        raise FileNotFoundError(f"nav_templates.{key} não configurado")
    return template_path_for(var)


def _search_region():
    return (
        cfg["search_region"]["x"].get(),
        cfg["search_region"]["y"].get(),
        cfg["search_region"]["width"].get(),
        cfg["search_region"]["height"].get(),
    )


def _save_debug_screenshot(label: str):
    """Salva screenshot da região de busca em logs/ para diagnóstico."""
    try:
        from datetime import datetime
        from PIL import ImageGrab
        from utils.global_variables import BASE_DIR
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(exist_ok=True)
        region = _search_region()
        x, y, w, h = region
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        ts = datetime.now().strftime("%H-%M-%S")
        path = logs_dir / f"debug_{label}_{ts}.png"
        img.save(str(path))
        debug(f"Screenshot salvo: {path.name}")
    except Exception as e:
        debug(f"Screenshot falhou: {e}")


def _header_region(max_h: int):
    """Faixa estreita no topo da região de busca — onde ficam botão de
    dificuldade e abas Act. Evita falsos positivos no conteúdo do mapa."""
    x = cfg["search_region"]["x"].get()
    y = cfg["search_region"]["y"].get()
    w = cfg["search_region"]["width"].get()
    full_h = cfg["search_region"]["height"].get()
    return (x, y, w, min(max_h, full_h))


def _update_mr_status():
    if gv.mr_status_label is not None:
        gv.mr_status_label.configure(text=gv.mr_status_message)
