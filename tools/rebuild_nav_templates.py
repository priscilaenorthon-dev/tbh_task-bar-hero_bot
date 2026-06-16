"""
Reconstrói TODOS os templates de navegação usando as imagens originais de captures/.

O que faz:
  1. Copia diff_normal / diff_nightmare / diff_hell → difficulty_*.png (botão fechado)
  2. Usa diff_hell como difficulty_dropdown.png
  3. Copia act1_active / act2_active / act3_active → act*.png
  4. Re-extrai linhas do dropdown aberto (diff_open_1/2/3) → difficulty_*_open.png
  5. Gera cópias _2 de todos os templates de navegação

Executa: python tools/rebuild_nav_templates.py
"""
import shutil
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

ROOT     = Path(__file__).resolve().parent.parent
ASSETS   = ROOT / "assets"
CAPTURES = ASSETS / "captures"


def _load(name):
    p = CAPTURES / name
    if not p.exists():
        print(f"  [SKIP] {name} não encontrado em captures/")
        return None
    return np.array(Image.open(p).convert("RGB"))


def _save(rgb, name):
    if rgb is None:
        return
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    out = ASSETS / name
    cv2.imwrite(str(out), bgr)
    h, w = rgb.shape[:2]
    print(f"  OK  {name}  ({w}×{h}px)")


def _copy(src_name, dst_name):
    src = CAPTURES / src_name
    dst = ASSETS / dst_name
    if not src.exists():
        print(f"  [SKIP] {src_name} não encontrado")
        return False
    shutil.copy2(src, dst)
    img = Image.open(dst)
    print(f"  OK  {dst_name}  ({img.width}×{img.height}px)")
    return True


def _find_highlighted_row(img, n=3):
    """Índice da linha com fundo laranja/marrom (opção selecionada no dropdown)."""
    if img is None:
        return -1
    h = img.shape[0]
    rh = h // n
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    best_idx, best_count = 0, 0
    for i in range(n):
        row_hsv = hsv[i * rh:(i + 1) * rh, :]
        mask = cv2.inRange(row_hsv, (5, 80, 60), (25, 255, 255))
        count = cv2.countNonZero(mask)
        if count > best_count:
            best_count, best_idx = count, i
    return best_idx


def _split_rows(img, n=3):
    if img is None:
        return [None] * n
    h = img.shape[0]
    rh = h // n
    return [img[i * rh:(i + 1) * rh, :] for i in range(n)]


def main():
    print("\n=== 1. Botões de dificuldade (fechados) ===")
    _copy("diff_normal.png",    "difficulty_normal.png")
    _copy("diff_nightmare.png", "difficulty_nightmare.png")
    _copy("diff_hell.png",      "difficulty_hell.png")
    # dropdown trigger = mesmo botão Hell
    _copy("diff_hell.png",      "difficulty_dropdown.png")

    print("\n=== 2. Abas Act (estado ativo) ===")
    _copy("act1_active.png", "act1.png")
    _copy("act2_active.png", "act2.png")
    _copy("act3_active.png", "act3.png")

    print("\n=== 3. Dropdown aberto — opções individuais ===")
    # diff_open_1: Hell destacado → Normal(0) e Nightmare(1) não-destacados
    img1 = _load("diff_open_1.png")
    hi1  = _find_highlighted_row(img1)
    rows1 = _split_rows(img1)
    print(f"  diff_open_1: linha destacada={hi1} (esperado 2=Hell)")
    _save(rows1[0], "difficulty_normal_open.png")
    _save(rows1[1], "difficulty_nightmare_open.png")

    # diff_open_2: Nightmare destacado → Hell(2) não-destacado
    img2 = _load("diff_open_2.png")
    hi2  = _find_highlighted_row(img2)
    rows2 = _split_rows(img2)
    print(f"  diff_open_2: linha destacada={hi2} (esperado 1=Nightmare)")
    _save(rows2[2], "difficulty_hell_open.png")

    print("\n=== 4. Cópias _2 (window_scale=2) ===")
    NAV = [
        "act1.png", "act2.png", "act3.png",
        "difficulty_normal.png", "difficulty_nightmare.png",
        "difficulty_hell.png", "difficulty_dropdown.png",
        "difficulty_normal_open.png", "difficulty_nightmare_open.png",
        "difficulty_hell_open.png",
    ]
    import re
    NAV += [p.name for p in ASSETS.glob("map_*.png")
            if re.match(r"map_\d-\d+\.png$", p.name)]

    created = 0
    for name in NAV:
        src = ASSETS / name
        if not src.exists():
            continue
        stem = Path(name).stem
        dst  = ASSETS / f"{stem}_2{Path(name).suffix}"
        shutil.copy2(src, dst)
        created += 1

    print(f"  {created} cópias _2 geradas")
    print("\nConcluído.")


if __name__ == "__main__":
    main()
