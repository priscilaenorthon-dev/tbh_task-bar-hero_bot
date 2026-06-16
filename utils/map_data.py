ACT1 = {
    "1-1":  "Pasto",
    "1-2":  "Prado das Sombras",
    "1-3":  "Terra Devastada",
    "1-4":  "Cânion Sinistro",
    "1-5":  "Entrada da Vila em Chamas",
    "1-6":  "Praça Rumstreet",
    "1-7":  "Arredores da Cidade",
    "1-8":  "Cemitério",
    "1-9":  "Terra Amaldiçoada",
    "1-10": "Trono das Trevas",
}

ACT2 = {
    "2-1":  "Estrada do Oásis",
    "2-2":  "Vale da Tempestade de Areia",
    "2-3":  "Caverna Subterrânea do Deserto",
    "2-4":  "Ninho de Insetos",
    "2-5":  "Dunas Escaldantes",
    "2-6":  "Ruínas do Pôr do Sol",
    "2-7":  "Areias da Meia-Noite",
    "2-8":  "Túmulo Sagrado",
    "2-9":  "Cripta do Faraó",
    "2-10": "Subcanal do Faraó",
}

ACT3 = {
    "3-1":  "Posto Avançado Nevado",
    "3-2":  "Campo de Batalha Congelado",
    "3-3":  "Entrada da Caverna Glacial",
    "3-4":  "Caverna da Geleira Congelada",
    "3-5":  "Portal do Inferno",
    "3-6":  "Ravina em Chamas",
    "3-7":  "Planícies do Tormento",
    "3-8":  "Cidadela em Ruínas",
    "3-9":  "Núcleo do Abismo",
    "3-10": "Câmara de Comando do Inferno",
}

ACTS = {
    "1": ACT1,
    "2": ACT2,
    "3": ACT3,
}

ALL_MAP_CODES = list(ACT1) + list(ACT2) + list(ACT3)


def map_label(code: str) -> str:
    act = code.split("-")[0]
    name = ACTS.get(act, {}).get(code, "")
    return f"{code} | {name}" if name else code


def template_for(code: str) -> str:
    return f"assets/map_{code}.png"


def act_of(code: str) -> str:
    return code.split("-")[0]
