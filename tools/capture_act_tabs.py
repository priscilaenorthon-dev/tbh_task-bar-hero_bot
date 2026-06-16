"""
Recaptura os templates das abas Act 1/2/3 no estado INATIVO (escuro).

Use assim — para cada aba, deixe ela INATIVA (não selecionada) no portal:

  Para capturar act1 inativo: abra o portal com Act 2 ou Act 3 selecionado, execute:
    python tools/capture_act_tabs.py --act 1

  Para act2 inativo: selecione Act 1 ou Act 3, execute:
    python tools/capture_act_tabs.py --act 2

  Para act3 inativo: selecione Act 1 ou Act 2, execute:
    python tools/capture_act_tabs.py --act 3

  Para todas de uma vez (deixe Act 2 ativo, então act1 e act3 serão inativos):
    python tools/capture_act_tabs.py --all

O script aguarda 5 segundos para você focar o jogo.
"""

import argparse
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Região das abas Act no portal (ajuste conforme sua resolução)
# Cobre a área horizontal das 3 abas na tela ultrawide
_TABS_REGION = (2100, 295, 2580, 365)  # (left, top, right, bottom)

# Posições aproximadas de cada aba dentro da região
_ACT_POSITIONS = {
    "1": (75,  35),  # cx, cy dentro da região capturada
    "2": (215, 35),
    "3": (360, 35),
}
_HALF_W = 65
_HALF_H = 26


def capture_tab(act: str):
    region = _TABS_REGION
    img = ImageGrab.grab(bbox=region)
    rgb = np.array(img)

    cx, cy = _ACT_POSITIONS[act]
    x1 = max(0, cx - _HALF_W)
    y1 = max(0, cy - _HALF_H)
    x2 = min(rgb.shape[1], cx + _HALF_W)
    y2 = min(rgb.shape[0], cy + _HALF_H)
    crop = rgb[y1:y2, x1:x2]
    bgr  = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)

    out = ASSETS / f"act{act}.png"
    cv2.imwrite(str(out), bgr)
    print(f"  Salvo: {out.name}  ({crop.shape[1]}x{crop.shape[0]}px)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--act", choices=["1", "2", "3"], help="Qual aba capturar")
    parser.add_argument("--all", action="store_true", help="Captura act1 e act3 (Act 2 deve estar ativo)")
    args = parser.parse_args()

    print("Aguardando 5 segundos — alterne para o jogo com o portal aberto...")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("Capturando!\n")

    if args.all:
        for a in ["1", "2", "3"]:
            capture_tab(a)
    elif args.act:
        capture_tab(args.act)
    else:
        print("Use --act 1|2|3 ou --all")


if __name__ == "__main__":
    main()
