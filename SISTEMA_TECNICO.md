# TBH Helper — Documentação Técnica do Sistema

Referência técnica completa do projeto. Use este documento para entender a arquitetura, adicionar funcionalidades e continuar o desenvolvimento com o Codex ou qualquer agente de IA.

---

## Visão geral

**TBH Helper** é um bot de automação para o jogo Task Bar Hero (Windows). Ele usa reconhecimento de imagem via OpenCV para localizar botões na tela do jogo e simula cliques e teclas via API do Windows (Win32). A interface gráfica é feita em Tkinter.

O sistema tem **duas funcionalidades principais**:

1. **Automação de Stash** — ciclo contínuo: abrir baú → auto fill → stash all → fechar
2. **Map Runner** — navegação automática de mapas com seleção de dificuldade e ato

---

## Stack de tecnologia

| Componente | Tecnologia | Versão mínima |
|---|---|---|
| Linguagem | Python | 3.10+ |
| GUI | tkinter (stdlib) | — |
| Reconhecimento de imagem | OpenCV (`opencv-python`) | 4.5.3.56 |
| Captura de tela | Pillow (`ImageGrab`) | 8.3.2 |
| Processamento numérico | NumPy | 1.21.2 |
| Input (mouse/teclado) | pywin32 (Win32 API) | 301 |
| Configuração | PyYAML | 5.4.1 |
| Build (.exe) | PyInstaller | qualquer recente |
| CI/CD | GitHub Actions | — |
| Plataforma | Windows only | — |

---

## Estrutura de arquivos

```
tbh_task-bar-hero_bot/
├── main.py                          # Ponto de entrada
├── requirements.txt                 # Dependências pip
├── Iniciar TBH Helper.bat           # Atalho Windows para iniciar o bot
│
├── gui/
│   ├── gui_initializer.py           # Cria a janela Tkinter principal
│   ├── stash_panel.py               # Todas as abas (Tela, Temporização, Executar, Caça ao Baú)
│   └── gui_functions.py             # Overlay de desenho de região, diagnóstico, start/stop
│
├── functionality/
│   ├── stash_loop.py                # Máquina de estados principal (stash + combine)
│   ├── image_search.py              # Busca de template via OpenCV
│   ├── map_runner_loop.py           # Loop de navegação de mapas
│   └── function_tester.py           # Diagnóstico não destrutivo
│
├── utils/
│   ├── global_variables.py          # Estado de runtime: flags, step index, status
│   ├── config.py                    # Carregamento de config, resolução de paths, randomização
│   ├── process_title.py             # Título da janela/console no Windows
│   └── map_data.py                  # Base de dados de mapas (30 mapas × 3 atos)
│
├── wrappers/
│   ├── win32api_wrapper.py          # Click, right-click, espaço, scroll via pywin32
│   └── logging_wrapper.py           # Logger centralizado com nível configurável
│
├── tools/                           # Utilitários para capturar/extrair assets
│   ├── capture_act_tabs.py
│   ├── capture_map_nodes.py
│   ├── extract_node_templates.py
│   └── rebuild_nav_templates.py
│
├── resources/
│   └── config.yml                   # Configuração persistida do usuário
│
├── assets/                          # 123 PNGs de template (900K total)
│   ├── auto_fill.png, auto_fill_1-25.png, auto_fill_1-50.png, auto_fill_2.png
│   ├── stash_all.png, stash_all_*.png
│   ├── sort.png, sort_*.png
│   ├── back_arrow.png, back_arrow_*.png
│   ├── chest_icon.png, boss_chest_icon.png
│   ├── combine.png, combine_*.png
│   ├── map_1-1.png … map_3-10.png   # 30 ícones de nó de mapa
│   ├── map_*_2.png                  # Variantes em escala 2×
│   ├── difficulty_normal.png, difficulty_nightmare.png, …
│   └── act1.png, act2.png, act3.png
│
├── docs/
│   └── automation.md                # Documentação da arquitetura de automação
│
└── .github/workflows/
    └── release.yml                  # Build automático de .exe e criação de release
```

---

## Arquitetura geral

```
main.py
  └─► gui_initializer.gui_init()
        └─► stash_panel()         ← cria 4 abas
              └─► root.mainloop() ← loop tkinter

Usuário clica "Iniciar Stash"
  └─► reset_stash_state()
  └─► stash_loop()               ← máquina de estados principal
  └─► start_periodic_stash_sort() ← loop paralelo em segundo plano
```

Toda a automação usa `tkinter.after()` — **sem threads**. Os loops agendam a próxima execução via callbacks.

---

## Máquina de estados — Stash Loop

**Arquivo:** `functionality/stash_loop.py`

### Variáveis de estado (`utils/global_variables.py`)

| Variável | Tipo | Significado |
|---|---|---|
| `continue_stash` | bool | `True` enquanto a automação está rodando |
| `current_step_index` | int | Índice do passo atual na lista `steps` do config |
| `step_wait_deadline` | float/None | `time.monotonic()` até quando esperar por um template |
| `combine_check_pending` | bool | `True` após clique no auto_fill até verificar combine |
| `status_message` | str | Texto exibido no rodapé da GUI |

### Sequência de passos (do `resources/config.yml`)

| Índice | Nome | Template | Clique |
|---|---|---|---|
| 0 | `open_chest` | `chest_check` (boss e normal) | Botão direito |
| 1 | `auto_fill` | `auto_fill.png` | Botão esquerdo → sub-fluxo combine |
| 2 | `stash_all` | `stash_all.png` | Botão esquerdo |
| 3 | `close_stash` | `back_arrow.png` | Botão esquerdo |

Após `close_stash`, o índice volta para 0 via módulo (`% len(steps)`).

### Diagrama de estados

```
open_chest → auto_fill → stash_all → close_stash → (volta ao open_chest)
                │
                ├─ combine encontrado → clica combine → clica voltar → RESTART (índice 0)
                │
                └─ combine NÃO encontrado → vai direto para stash_all
```

### Sub-fluxo Combine

1. Aguarda `combine_flow.wait` segundos (aleatório)
2. Verifica se template `combine.png` apareceu na tela
   - **Não apareceu:** pula direto para `stash_all`
   - **Apareceu:** clica combine → verifica `back_arrow`
     - `back_arrow` encontrado → clica → `_restart_loop()` (índice = 0)
     - `back_arrow` não encontrado → polling com `timeouts.loop` até `step_wait` expirar → pula para `stash_all`

### Funções de transição

| Função | Efeito |
|---|---|
| `_advance_to_next_step(name)` | `(índice + 1) % n` após ação bem-sucedida |
| `_skip_to_next_step(label)` | Mesmo cálculo, após timeout; loga aviso |
| `_restart_loop(msg)` | `índice = 0`; somente após combine+voltar bem-sucedido |

---

## Loop periódico de Stash/Sort

**Arquivo:** `functionality/stash_loop.py` → `periodic_stash_sort_loop()`

Roda em paralelo com a máquina principal, a cada 28–32 segundos (aleatório):

```
periodic_stash_sort_loop
  └─► procura stash_all → clica (se encontrar)
  └─► procura sort → clica (se encontrar)
  └─► pressiona espaço
  └─► agenda próxima execução
```

- Não modifica `current_step_index`
- Templates ausentes: pula o clique; não interrompe o loop principal

---

## Pipeline de reconhecimento de imagem

**Arquivo:** `functionality/image_search.py`

### Função principal: `find_template(region, template_path, threshold)`

```
region (x, y, w, h) em coordenadas de tela
  └─► ImageGrab.grab(bbox)        → screenshot BGR (NumPy)
  └─► cv.imread(template_path)    → template PNG (NumPy)
  └─► cv.matchTemplate(TM_CCOEFF_NORMED)
  └─► score máximo + localização
  └─► score >= threshold?
        sim → retorna (center_x, center_y, score) em pixels de tela
        não → retorna None
```

### Retornos

| Retorno | Significado |
|---|---|
| `(cx, cy, score)` | Centro do melhor match em pixels de tela |
| `None` | Abaixo do threshold, template ilegível, ou região menor que o template |

---

## Resolução de paths de template

**Arquivo:** `utils/config.py`

Os nomes no `config.yml` são **apenas o nome base** (ex: `auto_fill.png`). O sufixo de escala é resolvido em runtime:

| Escala (`window_scale`) | Sufixo | Exemplo |
|---|---|---|
| `1` | *(nenhum)* | `auto_fill.png` |
| `1.25` | `_1-25` | `auto_fill_1-25.png` |
| `1.5` | `_1-50` | `auto_fill_1-50.png` |
| `2` | `_2` | `auto_fill_2.png` |

**Funções principais:**

| Função | Faz |
|---|---|
| `base_template_name(var)` | Remove sufixo de escala se presente |
| `scaled_template_name(var)` | Adiciona sufixo baseado em `window_scale` |
| `template_path_for(var)` | Retorna path absoluto; alerta e usa base se variante escalada não existir |
| `step_entries()` | Lista de dicts com nome/path de cada step |
| `chest_check_entries()` | Lista de dicts dos templates de baú |

---

## Entrada de mouse e teclado

**Arquivo:** `wrappers/win32api_wrapper.py`

| Função | Ação |
|---|---|
| `click_mouse_with_coordinates(x, y)` | Move cursor → botão esquerdo (50ms entre down/up) |
| `right_click_mouse_with_coordinates(x, y)` | Botão direito (usado para abrir baú) |
| `space_bar()` | Pressiona espaço (usado no loop periódico) |
| `scroll_at(x, y, delta)` | Scroll do mouse (usado no Map Runner) |

Os cliques na `stash_loop.py` aplicam jitter aleatório via `random_click_offset()` antes de chamar as funções do wrapper.

---

## Configuração (`resources/config.yml`)

### Estrutura principal

```yaml
search_region:
  x: 1370
  y: 76
  width: 1288
  height: 1260

matching:
  threshold: 0.7        # 0–1; maior = mais estrito

timeouts:
  loop:       {min: 1.2, max: 1.8}   # intervalo entre tentativas (segundos)
  after_click:{min: 0.8, max: 1.4}   # pausa após clique
  step_wait:  {min: 45,  max: 60}    # timeout máximo por etapa

combine_flow:
  wait:          {min: 2.5, max: 3.5}
  template:      combine.png
  back_template: back_arrow.png

periodic_stash_sort:
  interval:       {min: 28, max: 32}
  between_clicks: {min: 0.2, max: 0.6}
  stash_template: stash_all.png
  sort_template:  sort.png

randomization:
  click_offset_px: {min: -8, max: 8}

chest_check:
  templates:
    - {name: boss_chest, template: boss_chest_icon.png}
    - {name: chest,      template: chest_icon.png}

steps:
  - {name: open_chest}
  - {name: auto_fill,    template: auto_fill.png}
  - {name: stash_all,    template: stash_all.png}
  - {name: close_stash,  template: back_arrow.png}

log_lvl: ERROR
window_scale: "1"

map_runner:
  chest_respawn_minutes: 5
  time_per_map: 120
  nav_click_delay: {min: 0.5, max: 1.0}
  difficulty: normal
  selected_maps: []
  nav_templates: {...}
```

### Como o config é carregado

Em `utils/config.py`, o YAML é lido na importação e todos os valores são encapsulados em variáveis Tkinter (`IntVar`, `DoubleVar`, `StringVar`). Widgets da GUI se ligam diretamente a essas variáveis. Na saída do app, `save_data()` escreve os valores de volta no YAML.

---

## Map Runner

**Arquivo:** `functionality/map_runner_loop.py`

Funcionalidade secundária acessível pela aba "Caça ao Baú".

### Capacidades

- **30 mapas** disponíveis em **3 atos**
- **4 dificuldades:** Normal, Nightmare, Hell, Torment
- Timer de respawn de baús configurável
- Tempo máximo por mapa configurável
- Clique automático em baús (boss e normal) durante a corrida
- Templates de ícone de nó de mapa para cada mapa (`map_1-1.png` até `map_3-10.png`)
- Variantes em escala 2× para displays de alta resolução

### Base de dados de mapas

**Arquivo:** `utils/map_data.py` — dicionário com os 30 mapas divididos em 3 atos. Usado para popular os checkboxes da aba e resolver qual template de nó usar.

---

## GUI — Interface Gráfica

**Framework:** Tkinter com `ttk.Notebook` (abas)

### Abas

| Aba | Conteúdo |
|---|---|
| **Tela** | Desenhar região, visualizar, escala de UI, threshold de matching |
| **Temporização** | Todos os timers (min/max em segundos) |
| **Executar** | Botões Iniciar/Parar, nível de log, diagnóstico, status |
| **Caça ao Baú** | Checkboxes de mapas, dificuldade, timers do Map Runner, status |

**Rodapé fixo:** Label de status sempre visível (atualizado em tempo real).

### Overlay de desenho de região

Em `gui/gui_functions.py`: janela transparente em tela cheia com `-alpha`. O usuário arrasta para selecionar a região. Não usa `-transparentcolor` (cliques passam pelo transparente no Windows, causando bugs).

---

## Diagnóstico

**Arquivo:** `functionality/function_tester.py`

Verificação não destrutiva (sem cliques). Testa:

- Tamanho mínimo da região (≥ 20px)
- Captura de tela funciona
- Arquivos de template existem e são legíveis
- Cada template configurado aparece na região (acima do threshold)
- Win32 (mouse/teclado) está acessível
- Integridade da sequência de passos

Resultados: `[OK]`, `[AVISO]` (não encontrou na tela), `[FALHA]` (erro crítico).

---

## CI/CD e Build

**Arquivo:** `.github/workflows/release.yml`

Trigger: tag `v*` no branch `main`.

```
git tag v1.0.0
git push origin v1.0.0
  └─► GitHub Actions (Windows runner)
        └─► pip install pyinstaller + requirements.txt
        └─► pyinstaller → dist/TBHHelper/
        └─► zip TBHHelper-Windows.zip
        └─► cria GitHub Release com o .zip
```

Para mais detalhes sobre releases: `RELEASES.md`.

---

## Logging

**Arquivo:** `wrappers/logging_wrapper.py`

- Logger único compartilhado por todos os módulos
- Nível configurável pelo usuário (DEBUG / INFO / WARNING / ERROR)
- Aplicado ao clicar "Iniciar Stash" via `apply_log_level()`
- Saída: console (padrão) + arquivo opcional no Map Runner

---

## Randomização anti-detecção

Todos os delays e coordenadas de clique são randomizados:

| Tipo | Implementação |
|---|---|
| Delays | `random.uniform(min, max)` em segundos; convertido para ms via `random_delay_ms()` |
| Coordenadas | `random_click_offset()` adiciona `random.randint(offset.min, offset.max)` ao centro do template |

Funções em `utils/config.py`: `random_timeout()`, `random_delay_ms()`, `random_click_offset()`.

---

## Padrões de código

- **Sem threads** — toda automação usa `tkinter.after()` (callbacks)
- **Funções simples** — sem classes de abstração desnecessárias
- **Dicts e variáveis globais** para estado de runtime (`gv.*`)
- **YAML como schema de configuração** — valores em runtime ficam em `IntVar`/`DoubleVar`/`StringVar`
- **Português** — strings de UI, logs e variáveis documentadas em português
- **Sem `.env`** — sem segredos; configuração apenas em `config.yml`

---

## Como adicionar novas funcionalidades

### Novo passo no ciclo de stash

1. Adicione em `resources/config.yml` → `steps`:
   ```yaml
   - {name: meu_passo, template: meu_template.png}
   ```
2. Adicione o PNG em `assets/` (e variantes escaladas se necessário)
3. Se o passo tiver comportamento especial, adicione branch em `functionality/stash_loop.py` (verificando `step["name"] == "meu_passo"`)

### Novo template

1. Adicione o PNG em `assets/` (base + variantes `_1-25`, `_1-50`, `_2` se necessário)
2. Referencie pelo nome base no YAML (ex: `meu_template.png`)
3. Use `template_path_for()` para resolver o path em runtime

### Nova aba na GUI

1. Adicione a função de criação da aba em `gui/stash_panel.py`
2. Chame na função principal de criação do painel
3. Adicione variáveis de config em `utils/config.py` e `resources/config.yml`

### Nova configuração

1. Adicione em `resources/config.yml` com valor padrão
2. Em `utils/config.py`, carregue como `IntVar`/`DoubleVar`/`StringVar` no dict de config
3. Adicione widget correspondente na aba correta em `gui/stash_panel.py`
4. Inclua na `save_data()` se precisar persistir

### Novo mapa no Map Runner

- Edite `utils/map_data.py` adicionando o mapa ao dicionário do ato correspondente
- Adicione os templates PNG em `assets/` (`map_X-Y.png` e `map_X-Y_2.png`)

---

## Mapa de arquivos por responsabilidade

| Responsabilidade | Arquivo |
|---|---|
| Ponto de entrada | `main.py` |
| Máquina de estados stash | `functionality/stash_loop.py` |
| Reconhecimento de imagem | `functionality/image_search.py` |
| Paths, escala, lista de passos | `utils/config.py` |
| Flags e estado de runtime | `utils/global_variables.py` |
| Configuração persistida | `resources/config.yml` |
| Start/stop da automação | `gui/gui_functions.py` |
| Criação das abas | `gui/stash_panel.py` |
| Entrada Windows (mouse/teclado) | `wrappers/win32api_wrapper.py` |
| Logging | `wrappers/logging_wrapper.py` |
| Map Runner | `functionality/map_runner_loop.py` |
| Base de dados de mapas | `utils/map_data.py` |
| Build e release | `.github/workflows/release.yml` + `RELEASES.md` |

---

## Referências internas

- `README.md` — guia do usuário (como instalar, configurar e usar)
- `AGENTS.md` — convenções para agentes de IA trabalhando no repositório
- `docs/automation.md` — diagramas detalhados da máquina de estados e do matcher
- `RELEASES.md` — instruções de build e publicação de releases
