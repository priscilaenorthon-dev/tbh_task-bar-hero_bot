from pathlib import Path

import win32api

from functionality.image_search import grab_region, probe_template
from utils.config import (
    chest_check_entries,
    dict,
    step_entries,
    template_path_for,
)
from wrappers.logging_wrapper import info

_MIN_REGION_SIZE = 20

Result = tuple[str, str, str]  # (check_name, status, detail) — status: PASS | WARN | FAIL


def run_diagnostics() -> list[Result]:
    """Executa verificações não-destrutivas (sem cliques). Retorna lista de (nome, status, detalhe)."""
    results: list[Result] = []
    threshold = dict["matching"]["threshold"].get()
    region = _search_region()

    results.append(_check_search_region(region))
    screenshot_cv, capture_result = _check_screen_capture(region)
    results.append(capture_result)

    if screenshot_cv is None:
        results.extend(_check_template_files_only())
        results.append(_check_win32_input())
        _log_summary(results)
        return results

    results.extend(_check_game_screens(screenshot_cv, region, threshold))

    for label, template_path in _configured_templates():
        results.append(
            _check_template_match(label, screenshot_cv, region, template_path, threshold)
        )

    results.append(_check_win32_input())
    results.append(_check_stash_steps())
    _log_summary(results)
    return results


def _search_region():
    return (
        dict["search_region"]["x"].get(),
        dict["search_region"]["y"].get(),
        dict["search_region"]["width"].get(),
        dict["search_region"]["height"].get(),
    )


def _configured_templates():
    items: list[tuple[str, str]] = []
    for chest in chest_check_entries():
        items.append((f"chest:{chest['name']}", chest["template"]))
    for step in step_entries():
        if "template" in step:
            items.append((f"step:{step['name']}", step["template"]))
    items.append(("combine", template_path_for(dict["combine_flow"]["template"])))
    items.append(("combine_back", template_path_for(dict["combine_flow"]["back_template"])))
    items.append(
        ("periodic_stash", template_path_for(dict["periodic_stash_sort"]["stash_template"]))
    )
    items.append(
        ("periodic_sort", template_path_for(dict["periodic_stash_sort"]["sort_template"]))
    )
    return items


def _check_search_region(region) -> Result:
    _x, _y, width, height = region
    if width < _MIN_REGION_SIZE or height < _MIN_REGION_SIZE:
        return (
            "Região de busca",
            "FAIL",
            f"Região {width}x{height} - configure na aba Tela (mín {_MIN_REGION_SIZE}px)",
        )
    return (
        "Região de busca",
        "PASS",
        f"{width}x{height} em ({_x}, {_y})",
    )


def _check_screen_capture(region):
    try:
        screenshot_cv = grab_region(region)
        h, w = screenshot_cv.shape[:2]
        return screenshot_cv, ("Captura de tela", "PASS", f"Frame BGR {w}x{h} capturado")
    except Exception as exc:
        return None, ("Captura de tela", "FAIL", str(exc))


def _check_template_files_only() -> list[Result]:
    results = []
    for label, template_path in _configured_templates():
        path = Path(template_path)
        if path.is_file():
            results.append((f"Arquivo de template ({label})", "PASS", path.name))
        else:
            results.append((f"Arquivo de template ({label})", "FAIL", f"Ausente: {path}"))
    return results


def _check_template_match(label, screenshot_cv, region, template_path, threshold) -> Result:
    path = Path(template_path)
    if not path.is_file():
        return (f"Buscador de imagem ({label})", "FAIL", f"Arquivo ausente: {path.name}")

    probe = probe_template(screenshot_cv, region, template_path, threshold)
    if probe["error"]:
        return (f"Buscador de imagem ({label})", "FAIL", probe["error"])

    score = probe["score"]
    name = path.name
    if probe["found"]:
        cx, cy = probe["center"]
        return (
            f"Buscador de imagem ({label})",
            "PASS",
            f"{name} score {score:.3f} em ({cx}, {cy})",
        )

    return (
        f"Buscador de imagem ({label})",
        "WARN",
        f"{name} melhor score {score:.3f} (threshold {threshold:.2f}) - não visível na região",
    )


def _check_win32_input() -> Result:
    try:
        x, y = win32api.GetCursorPos()
        return ("Entrada Win32", "PASS", f"Cursor em ({x}, {y}); cliques não testados")
    except Exception as exc:
        return ("Entrada Win32", "FAIL", str(exc))


def _check_stash_steps() -> Result:
    steps = step_entries()
    if not steps:
        return ("Etapas de stash", "FAIL", "Nenhuma etapa configurada em config.yml")
    names = ", ".join(step["name"] for step in steps)
    return ("Etapas de stash", "PASS", names)


def _step_template_path(step_name: str) -> str | None:
    for step in dict["steps"]:
        if step["name"] == step_name and "template" in step:
            try:
                return template_path_for(step["template"])
            except Exception:
                return None
    return None


def _combine_template_path() -> str | None:
    try:
        return template_path_for(dict["combine_flow"]["template"])
    except Exception:
        return None


def _check_game_screens(screenshot_cv, region, threshold) -> list[Result]:
    """Verifica se as 3 telas necessárias para o stash estão abertas."""
    checks = [
        (
            "Tela: Inventário do personagem",
            _step_template_path("auto_fill"),
            "Abra o inventário do personagem no jogo",
        ),
        (
            "Tela: Depósito",
            _step_template_path("stash_all"),
            "Abra a tela de depósito no jogo",
        ),
        (
            "Tela: Refinamento",
            _combine_template_path(),
            "Abra a tela de refinamento no jogo",
        ),
    ]
    results: list[Result] = []
    for label, tpl_path, hint in checks:
        if tpl_path is None:
            results.append((label, "FAIL", f"Template não configurado — {hint}"))
            continue
        probe = probe_template(screenshot_cv, region, tpl_path, threshold)
        if probe["error"]:
            results.append((label, "FAIL", probe["error"]))
        elif probe["found"]:
            cx, cy = probe["center"]
            results.append((label, "PASS", f"Visível em ({cx}, {cy}) — score {probe['score']:.3f}"))
        else:
            results.append(
                (label, "WARN", f"Não encontrada (score {probe['score']:.3f}) — {hint}")
            )
    return results


def _log_summary(results: list[Result]):
    passed = sum(1 for _, status, _ in results if status == "PASS")
    warned = sum(1 for _, status, _ in results if status == "WARN")
    failed = sum(1 for _, status, _ in results if status == "FAIL")
    info(f"Diagnóstico: {passed} ok, {warned} aviso, {failed} falha")
