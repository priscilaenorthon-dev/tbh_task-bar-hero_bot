"""
Extrai templates dos nós de cada Act a partir dos prints salvos em assets/captures/.
Executa: python tools/extract_node_templates.py
"""
import cv2
import numpy as np
from pathlib import Path
from PIL import Image

ROOT   = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CAPTURES = ASSETS / "captures"
HALF = 32  # crop 64x64

# Para cada arquivo: lista de códigos ordenados de BAIXO para CIMA na tela
# (blob com maior Y → primeiro código da lista)
CONFIGS = [
    # arquivo,                branco de baixo p/ cima,                       boss (círculo vermelho)
    ("act1_bottom.png", ["1-1","1-2","1-3","1-4","1-5","1-6","1-7"],    None),
    ("act1_top.png",    ["1-4","1-5","1-6","1-7","1-8","1-9"],          "1-10"),
    ("act2_bottom.png", ["2-1","2-2","2-3","2-4","2-5","2-6","2-7"],    None),
    ("act2_top.png",    ["2-4","2-5","2-6","2-7","2-8","2-9"],          "2-10"),
    ("act3_bottom.png", ["3-1","3-2","3-3","3-4","3-5","3-6","3-7"],    None),
    ("act3_top.png",    ["3-4","3-5","3-6","3-7","3-8","3-9"],          "3-10"),
]


def _load_rgb(path):
    img = Image.open(path).convert("RGB")
    return np.array(img)


def _white_blobs(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, (0, 0, 200), (180, 55, 255))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 60 or a > 4000:
            continue
        M = cv2.moments(c)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        blobs.append((cx, cy))
    # remove duplicatas (< 20px entre si)
    blobs.sort(key=lambda b: b[1])
    out = []
    for b in blobs:
        if out and abs(b[1] - out[-1][1]) < 20 and abs(b[0] - out[-1][0]) < 20:
            continue
        out.append(b)
    return out  # ordenados de cima para baixo (Y crescente)


def _red_blob(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    m1 = cv2.inRange(hsv, (0,  150, 150), (10,  255, 255))
    m2 = cv2.inRange(hsv, (160,150, 150), (180, 255, 255))
    mask = cv2.bitwise_or(m1, m2)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_a = 0
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 60 or a > 4000:
            continue
        if a > best_a:
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            best = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))
            best_a = a
    return best


def _save(rgb, cx, cy, code, skip_existing=False):
    out = ASSETS / f"map_{code}.png"
    if skip_existing and out.exists():
        print(f"    SKIP {out.name} (já existe)")
        return
    h, w = rgb.shape[:2]
    x1, y1 = max(0, cx-HALF), max(0, cy-HALF)
    x2, y2 = min(w, cx+HALF), min(h, cy+HALF)
    crop = rgb[y1:y2, x1:x2]
    bgr  = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(out), bgr)
    print(f"    OK  map_{code}.png  centro=({cx},{cy})  tamanho={crop.shape[1]}x{crop.shape[0]}")


def main():
    saved = 0
    for filename, white_codes, boss_code in CONFIGS:
        src = CAPTURES / filename
        if not src.exists():
            print(f"\n[SKIP] {filename} não encontrado")
            continue
        print(f"\n[{filename}]")
        rgb = _load_rgb(src)

        # Círculos brancos
        blobs = _white_blobs(rgb)
        # Ordenar de BAIXO para CIMA (Y decrescente → 1º da lista = stage mais baixo)
        blobs_bottom_first = sorted(blobs, key=lambda b: -b[1])
        print(f"  Blobs brancos detectados: {len(blobs_bottom_first)}")
        for i, (bx, by) in enumerate(blobs_bottom_first):
            print(f"    blob {i+1}: ({bx}, {by})")

        for i, code in enumerate(white_codes):
            if i >= len(blobs_bottom_first):
                print(f"    AVISO: sem blob para {code} (só {len(blobs_bottom_first)} detectados)")
                break
            bx, by = blobs_bottom_first[i]
            _save(rgb, bx, by, code)
            saved += 1

        # Círculo vermelho (boss)
        if boss_code:
            rb = _red_blob(rgb)
            if rb:
                print(f"  Boss vermelho detectado: {rb}")
                _save(rgb, rb[0], rb[1], boss_code)
                saved += 1
            else:
                print(f"  AVISO: blob vermelho não encontrado para {boss_code}")

    print(f"\n=== Concluído: {saved} templates salvos em assets/ ===")


if __name__ == "__main__":
    main()
