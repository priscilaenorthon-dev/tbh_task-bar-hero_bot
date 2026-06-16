import time
from pathlib import Path

import utils.global_variables as gv
from functionality.image_search import find_template
from functionality.stash_loop import reset_stash_state, start_periodic_stash_sort, stash_loop
from utils.config import dict as cfg, random_click_offset, random_delay_ms, random_timeout, template_path_for
from utils.map_data import act_of, map_label, template_for
from wrappers.logging_wrapper import debug, info, warning
from wrappers.win32api_wrapper import click_mouse_with_coordinates, scroll_at

_ACT_KEYS = {"1": "act1", "2": "act2", "3": "act3"}
_MAX_SCROLL_ATTEMPTS = 14
_SCROLL_DOWN = -120
_SCROLL_UP   =  120
# Stages com número ≤ 5 ficam no terço inferior do mapa (scroll down),
# stages ≥ 6 ficam no terço superior (scroll up).
_SCROLL_BOTTOM_STAGES = {1, 2, 3, 4, 5}


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
    """Seleciona a dificuldade correta no portal.

    Fase 0: verifica se a dificuldade já está correta (botão fechado visível).
    Fase 1: dropdown foi aberto — procura a opção alvo para clicar.
            Não clica no dropdown novamente para evitar loop abrir/fechar.
    """
    if not gv.continue_map_runner:
        return

    difficulty = cfg["map_runner"]["difficulty"].get().lower()
    template_key = difficulty if difficulty in ("normal", "nightmare", "hell", "torment") else "hell"
    _MAX_ATTEMPTS = 8

    def _proceed():
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                      lambda: _click_act_tab(code))

    # Botão de dificuldade fica em region y≈163 — usar altura mínima de 220px
    diff_region = _header_region(220)
    # Dropdown aberto mostra lista abaixo do botão
    open_region = _header_region(420)
    threshold = cfg["matching"]["threshold"].get()
    # Limiar mínimo para dificuldade — templates são parecidos, exige match mais alto
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

        # Não está correta → acha o botão testando TODOS os templates de dificuldade.
        # O botão mostra a dificuldade atual; qual template der maior score indica
        # a posição do botão mesmo que não seja o template certo.
        _DIFF_KEYS = ("normal", "nightmare", "hell", "torment", "difficulty_dropdown")
        _FIND_THRESHOLD = 0.65  # limiar baixo só para localizar o botão
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
    # Na primeira tentativa, salva screenshot para diagnóstico
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
            # Aguarda o dropdown fechar e confirma na fase 0
            gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                          lambda: _click_difficulty_dropdown(code, phase=0))
            return
    except FileNotFoundError:
        debug(f"Map Runner: template '{open_key}' não encontrado — execute tools/extract_open_dropdown_templates.py")

    if attempt >= _MAX_ATTEMPTS:
        warning(f"Map Runner: opção '{difficulty}' não encontrada no seletor — continuando assim mesmo")
        _proceed()
        return

    debug(f"Map Runner: aguardando opção '{difficulty}' no seletor (tentativa {attempt+1}/{_MAX_ATTEMPTS})...")
    gv.root.after(random_delay_ms(cfg["timeouts"]["loop"]),
                  lambda: _click_difficulty_dropdown(code, phase=1, attempt=attempt + 1))


_ACT_TAB_SPACING = 140  # pixels entre centros das abas (Act1→Act2→Act3)
_MAX_TAB_ATTEMPTS = 6


def _click_act_tab(code, attempt=0):
    """Navega para a aba do Act correto.

    Os templates das abas mostram o estado ATIVO (selecionado).
    Estratégia:
      1. Procura a aba alvo ativa  → já estamos no Act certo → vai para o nó.
      2. Procura qualquer outra aba ativa → calcula offset e clica na aba alvo.
      3. Após N tentativas sem encontrar nada → assume Act correto e continua.
    """
    if not gv.continue_map_runner:
        return

    act = act_of(code)
    target_num = int(act)
    # Abas Act ficam na mesma faixa horizontal do botão de dificuldade (region x≈794).
    # Usar largura completa mas restringir altura a 300px para não entrar no mapa.
    tab_region = _header_region(300)
    # Threshold mais permissivo para abas: o Act ativo sempre pontua maior que os outros,
    # então o "melhor score" já filtra corretamente sem precisar de limiar alto.
    threshold = min(0.55, cfg["matching"]["threshold"].get())

    def _go_to_node():
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                      lambda: _find_map_node(code, scroll_attempts=0))

    # Salva screenshot da região de busca na primeira tentativa para diagnóstico
    if attempt == 0:
        _save_debug_screenshot("act_tab_region")

    # Procura todos os Acts e usa o de MAIOR score como âncora ativa.
    # As abas têm aparência muito similar entre si (mesma cor laranja);
    # o template correto da aba ativa sempre pontua mais alto que os outros.
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

    # Failsafe: evita loop infinito se o Act nunca mudar
    if attempt >= _MAX_TAB_ATTEMPTS:
        warning(f"Map Runner: Act {act} não confirmado após {attempt} tentativas — continuando")
        _go_to_node()
        return

    # Calcula offset desde a aba encontrada até a aba alvo e clica
    ax, ay, _ = best_m
    offset = (target_num - int(best_act)) * _ACT_TAB_SPACING
    tx = ax + offset
    ox, oy = random_click_offset()
    click_mouse_with_coordinates(tx + ox, ay + oy)
    info(f"Map Runner: clicou Act {act} em ({tx},{ay}) via offset de Act {best_act} score={best_score:.3f}")
    # Aguarda UI atualizar e re-verifica se o Act correto ficou ativo antes de buscar o mapa
    gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]),
                  lambda: _click_act_tab(code, attempt + 1))


def _find_map_node(code, scroll_attempts):
    if not gv.continue_map_runner:
        return

    label = map_label(code)
    asset_path = template_for(code)

    # Build a StringVar-like proxy so template_path_for() works with scaled variants
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
        gv.root.after(random_delay_ms(cfg["map_runner"]["nav_click_delay"]), _start_stash_phase)
        return

    if scroll_attempts >= _MAX_SCROLL_ATTEMPTS:
        warning(f"Map Runner: nó '{label}' não encontrado após {_MAX_SCROLL_ATTEMPTS} scrolls — pulando")
        gv.mr_status_message = f"Mapa '{label}' não encontrado"
        _update_mr_status()
        _advance_to_next_map()
        return

    # Scroll na direção correta e tenta novamente
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


# ── STASH ─────────────────────────────────────────────────────────────────────

def _start_stash_phase():
    if not gv.continue_map_runner:
        return

    maps = _active_map_codes()
    current_idx = gv.mr_current_map_index % len(maps)
    label = map_label(maps[current_idx])

    duration_s = random_timeout(cfg["map_runner"]["time_per_map"])
    gv.mr_stash_phase_deadline = time.monotonic() + duration_s

    info(f"Map Runner: coletando em '{label}' por {duration_s:.1f}s")
    gv.mr_status_message = f"Coletando em {label} ({duration_s:.0f}s)..."
    _update_mr_status()

    gv.continue_stash = True
    reset_stash_state()
    stash_loop()
    start_periodic_stash_sort()

    gv.root.after(int(duration_s * 1000), _check_stash_phase_done)


def _check_stash_phase_done():
    if not gv.continue_map_runner:
        gv.continue_stash = False
        return

    if time.monotonic() >= gv.mr_stash_phase_deadline:
        _record_and_advance()
    else:
        remaining_ms = int((gv.mr_stash_phase_deadline - time.monotonic()) * 1000)
        gv.root.after(max(500, remaining_ms), _check_stash_phase_done)


# ── RECORD ────────────────────────────────────────────────────────────────────

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
