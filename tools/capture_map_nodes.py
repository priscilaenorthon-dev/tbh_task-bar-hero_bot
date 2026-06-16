"""
Captura automaticamente os templates dos nós do mapa do portal.

Uso:
  1. Abra o portal do jogo no Act desejado.
  2. Role o mapa para que os nós desejados estejam visíveis.
  3. Execute:

     python tools/capture_map_nodes.py --act 2 --codes 2-1,2-2,2-3,2-4,2-5,2-6,2-7

  Os códigos são listados de baixo para cima na tela (o nó mais abaixo
  na imagem recebe o primeiro código da lista).

  Para capturar a parte de cima (stages 2-8, 2-9, 2-10), role para cima e:
     python tools/capture_map_nodes.py --act 2 --codes 2-4,2-5,2-6,2-7,2-8,2-9,2-10

  O script NÃO sobrescreve um arquivo que já existe — use --force para sobrescrever.
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import ImageGrab

_ROOT = Path(__file__).resolve().parent.parent
_ASSETS = _ROOT / "assets"

# Região de busca padrão: o portal fica à direita na 3440×1440
# Ajuste conforme sua resolução / posição do portal.
_PORTAL_REGION = (1444, 68, 2798, 1034)  # (left, top, right, bottom)
_CROP_HALF = 32   # template salvo como 64×64 centrado no blob


def _grab_portal(region):
    img = ImageGrab.grab(bbox=region)
    return np.array(img)


def _find_circle_blobs(rgb):
    """Detecta centros dos círculos brancos dos nós usando máscara HSV."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    # Branco brilhante: S baixo, V alto
    mask = cv2.inRange(hsv, (0, 0, 200), (180, 60, 255))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 80 or area > 3000:
            continue
        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        blobs.append((cx, cy, area))

    # Remove duplicatas próximas (mesma região)
    blobs.sort(key=lambda b: b[1])  # ordena por Y
    filtered = []
    for b in blobs:
        if filtered and abs(b[1] - filtered[-1][1]) < 20 and abs(b[0] - filtered[-1][0]) < 20:
            continue
        filtered.append(b)

    return filtered


def _save_template(rgb, cx, cy, path, force):
    if path.exists() and not force:
        print(f"  Já existe: {path.name} (use --force para sobrescrever)")
        return False
    h, w = rgb.shape[:2]
    x1 = max(0, cx - _CROP_HALF)
    y1 = max(0, cy - _CROP_HALF)
    x2 = min(w, cx + _CROP_HALF)
    y2 = min(h, cy + _CROP_HALF)
    crop = rgb[y1:y2, x1:x2]
    bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr)
    print(f"  Salvo: {path.name} ({cx + _PORTAL_REGION[0]}, {cy + _PORTAL_REGION[1]})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Captura templates de nós do mapa.")
    parser.add_argument("--act", type=str, required=True, help="Número do Act (1, 2 ou 3)")
    parser.add_argument(
        "--codes",
        type=str,
        required=True,
        help="Códigos dos mapas visíveis, de BAIXO para CIMA, separados por vírgula. Ex: 2-1,2-2,2-3",
    )
    parser.add_argument("--force", action="store_true", help="Sobrescreve templates existentes")
    args = parser.parse_args()

    codes = [c.strip() for c in args.codes.split(",")]

    print(f"\nCapturando nós: {', '.join(codes)}")
    print(f"Região do portal: {_PORTAL_REGION}\n")

    rgb = _grab_portal(_PORTAL_REGION)
    blobs = _find_circle_blobs(rgb)

    print(f"Blobs detectados: {len(blobs)}")
    for i, (bx, by, area) in enumerate(blobs):
        screen_x = bx + _PORTAL_REGION[0]
        screen_y = by + _PORTAL_REGION[1]
        print(f"  blob {i+1}: screen=({screen_x}, {screen_y}) area={area:.0f}")

    # Ordena blobs de baixo para cima (Y maior = mais abaixo = menor stage number)
    blobs_sorted = sorted(blobs, key=lambda b: -b[1])  # Y decrescente = bottom-first

    if len(blobs_sorted) < len(codes):
        print(f"\nAVISO: {len(blobs_sorted)} blobs detectados mas {len(codes)} códigos fornecidos.")
        print("Role o mapa para ter mais nós visíveis, ou forneça menos códigos.")
        sys.exit(1)

    print(f"\nAssociando (de baixo para cima):")
    saved = 0
    for code, (bx, by, area) in zip(codes, blobs_sorted):
        screen_x = bx + _PORTAL_REGION[0]
        screen_y = by + _PORTAL_REGION[1]
        path = _ASSETS / f"map_{code}.png"
        print(f"  {code} ← blob em ({screen_x}, {screen_y})")
        if _save_template(rgb, bx, by, path, args.force):
            saved += 1

    print(f"\nConcluído: {saved} template(s) salvos em assets/")


if __name__ == "__main__":
    main()
