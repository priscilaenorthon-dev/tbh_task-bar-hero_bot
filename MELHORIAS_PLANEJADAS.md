# Plano de Melhorias — TBH Helper

## Contexto

O sistema já tem randomização de tempo e offset de clique, mas faltam mecanismos importantes de humanização (movimento gradual do mouse, duração variável do clique), melhorias visuais, contadores de baús por tipo e sessão, e facilidades de logging. Este plano organiza todas as melhorias por prioridade e impacto.

---

## Melhoria 1 — Humanização avançada (anti-ban)

### O que já existe
- Offset de clique ±8px (`utils/config.py` → `random_click_offset()`)
- Delays com min/max em todos os passos (`random_timeout`, `random_delay_ms`)
- 50ms fixo entre mouse-down e mouse-up nos cliques esquerdos

### O que falta (alto risco de detecção)
1. **Teleporte instantâneo do cursor** — `SetCursorPos()` em `wrappers/win32api_wrapper.py` move o mouse instantaneamente; sistemas anti-cheat detectam isso
2. **Right-click sem pausas** — `right_click_mouse_with_coordinates()` não tem delay entre down/up nem antes do clique
3. **Hold time fixo de 50ms** — todos os cliques têm exatamente 50ms de duração; humanos variam entre 30–120ms
4. **Space bar sem delay** — keydown/keyup imediatos sem pausa intermediária

### Implementação

**A. Movimento gradual do mouse com curva de Bezier**
- Arquivo: `wrappers/win32api_wrapper.py`
- Nova função: `_move_mouse_human(x2, y2)` — lê posição atual do cursor, gera 18–28 pontos intermediários numa curva de Bezier quadrática com ponto de controle aleatório deslocado, move o cursor por cada ponto com `time.sleep` variável (início lento, meio rápido, fim lento — curva de aceleração humana)
- Aplicar em: `click_mouse_with_coordinates()` e `right_click_mouse_with_coordinates()` antes de clicar
- Config nova em `resources/config.yml`:
  ```yaml
  mouse_movement:
    steps: {min: 18, max: 28}       # pontos da curva
    duration_ms: {min: 80, max: 200} # tempo total do movimento
  ```
- Adicionar campos na aba Temporização

**B. Click hold duration variável**
- Arquivo: `wrappers/win32api_wrapper.py`
- Substituir `time.sleep(0.05)` fixo por `time.sleep(random.uniform(0.03, 0.10))` em ambos os cliques
- Config nova:
  ```yaml
  click_hold_ms: {min: 30, max: 100}
  ```

**C. Right-click corrigido**
- Adicionar delay de posição (igual ao left-click) antes do clique
- Adicionar hold duration variável entre down/up

**D. Keyboard hold variável**
- Arquivo: `wrappers/win32api_wrapper.py` → `space_bar()`
- Adicionar `time.sleep(random.uniform(0.04, 0.09))` entre keydown e keyup
- Config nova:
  ```yaml
  keyboard_hold_ms: {min: 40, max: 90}
  ```

**E. Micro-pausas aleatórias no loop**
- Arquivo: `functionality/stash_loop.py`
- Com probabilidade 15%, antes de iniciar um passo, aguardar 200–800ms extra (simula distração humana)
- Config nova:
  ```yaml
  micro_pause:
    probability: 0.15
    duration_ms: {min: 200, max: 800}
  ```

---

## Melhoria 2 — Interface gráfica e design

### O que já existe
- Janela 500×560px, redimensionável, Segoe UI, tema tkinter padrão
- 4 abas com scroll, rodapé com status

### Mudanças

**A. Tamanho inicial maior**
- Arquivo: `gui/gui_initializer.py`
- Alterar `geometry("500x560")` → `geometry("680x660")`
- Alterar `minsize(480, 520)` → `minsize(600, 580)`
- Motivo: garantir que todos os botões e campos sejam visíveis sem scroll na abertura

**B. Tema ttk melhorado**
- Arquivo: `gui/gui_initializer.py`
- Aplicar `ttk.Style().theme_use("clam")` — visual mais moderno que o tema padrão
- Configurar cores dos botões: Iniciar → fundo verde `#2da44e`, Parar → fundo vermelho `#cf222e`, texto branco
- Aplicar em `gui/stash_panel.py` nos botões de start/stop

**C. Botões Start/Stop maiores e coloridos**
- Arquivo: `gui/stash_panel.py`
- Aumentar padding dos botões `pady=8, padx=20`
- Fonte maior: `("Segoe UI", 10, "bold")`
- Botão "Iniciar Stash" → verde | "Parar Stash" → vermelho

**D. Mini log de atividade na aba Executar**
- Arquivo: `gui/stash_panel.py`
- Adicionar um widget `Text` (somente leitura, 8 linhas) acima da área de diagnóstico mostrando as últimas ações do bot em tempo real (não substitui o log de arquivo)
- Quando o status mudar (`gv.status_message`), append a linha no mini log com timestamp
- Ref: variável `gv.activity_log_widget` nova em `global_variables.py`

---

## Melhoria 3 — Contador de baús (azul e marrom)

### O que já existe
- Templates distintos: `boss_chest_icon.png` (azul) e `chest_icon.png` (marrom) — já diferenciados
- `_handle_open_chest_step()` em `stash_loop.py` sabe qual tipo encontrou
- `gv.mr_current_map_index` rastreia o mapa atual no Map Runner

### Implementação

**A. Variáveis de contador** — `utils/global_variables.py`
```python
session_chest_count = 0       # baús marrons na sessão
session_boss_chest_count = 0  # baús azuis (boss) na sessão
chests_per_map = {}            # {map_name: {"chest": N, "boss_chest": N}}
```

**B. Incrementar ao abrir** — `functionality/stash_loop.py`
- Em `_handle_open_chest_step()`, na linha após o right-click bem-sucedido (~linha 119):
  - Se `chest["name"] == "boss_chest"`: `gv.session_boss_chest_count += 1`
  - Else: `gv.session_chest_count += 1`
  - Se Map Runner ativo: atualizar `gv.chests_per_map` com mapa atual

**C. Display na GUI** — `gui/stash_panel.py`
- Na aba "Executar", abaixo dos botões Start/Stop, adicionar frame "Contadores da sessão":
  ```
  🟤 Baús normais: 0    🔵 Baús boss: 0    Total: 0
  ```
- Labels: `gv.lbl_chest_count`, `gv.lbl_boss_chest_count`, `gv.lbl_total_count`
- Atualizar labels no mesmo callback que incrementa os contadores

**D. Resetar ao iniciar** — `gui/gui_functions.py`
- Na função `start_stash()`, zerar `gv.session_chest_count = 0` e `gv.session_boss_chest_count = 0`

**E. Resumo por mapa (aba Caça ao Baú)**
- Adicionar pequena seção "Baús por mapa nesta sessão" no Map Runner tab mostrando dict `chests_per_map` como texto atualizado

---

## Melhoria 4 — Logging melhorado

### O que já existe
- Map Runner cria `logs/map_runner_YYYY-MM-DD_HH-MM-SS.log` quando inicia
- Console handler sempre ativo
- Nível configurável pelo usuário

### Mudanças

**A. Stash também gera arquivo de log**
- Arquivo: `gui/gui_functions.py` → função `start_stash()`
- Ao iniciar stash, chamar `enable_file_logging(prefix="stash")` → cria `logs/stash_YYYY-MM-DD_HH-MM-SS.log`
- Ref: função `enable_file_logging()` já existe em `wrappers/logging_wrapper.py` (linha ~29)

**B. Rotação de logs (máximo 10 arquivos)**
- Arquivo: `wrappers/logging_wrapper.py`
- Após criar novo arquivo de log, verificar quantidade de arquivos em `logs/`
- Se mais de 10: deletar os mais antigos (`sorted by mtime`)

**C. Formato com módulo de origem**
- Arquivo: `wrappers/logging_wrapper.py`
- Alterar formatter:
  `"%(asctime)s [%(levelname)s] %(message)s"` → `"%(asctime)s [%(levelname)s] %(module)s: %(message)s"`

**D. Botão "Abrir pasta de logs" na aba Executar**
- Arquivo: `gui/stash_panel.py`
- Adicionar botão que chama `os.startfile(logs_dir)` — abre o Explorer na pasta de logs no Windows
- Mostrar o caminho atual do log em label pequeno abaixo do botão

**E. Mostrar caminho do log ativo na GUI**
- Label discreto exibindo `logs/stash_2026-06-16_07-13.log` após iniciar

---

## Melhoria 5 — Outros ajustes úteis

**A. Botão Pausar/Continuar**
- `gui/stash_panel.py` + `gui/gui_functions.py` + `utils/global_variables.py`
- Nova flag `gv.stash_paused = False`
- Botão "Pausar" que seta a flag; no próximo tick do `stash_loop()` a automação aguarda sem sair
- Útil para pausar momentaneamente sem perder o estado

**B. Ícone na barra de tarefas**
- `gui/gui_initializer.py`
- Verificar se existe um `.ico` em assets; se não, gerar um via `PIL.Image` e aplicar com `root.iconphoto()`

**C. Configuração exportar/importar**
- `gui/stash_panel.py` + `utils/config.py`
- Botões "Exportar config" e "Importar config" que fazem cópia/restauração do `resources/config.yml`
- Útil para manter perfis diferentes (ex: config para 1080p vs 4K)

---

## Arquivos a modificar (resumo)

| Arquivo | O que muda |
|---|---|
| `wrappers/win32api_wrapper.py` | Bezier movement, hold duration variável, right-click corrigido, keyboard timing |
| `utils/global_variables.py` | Contadores de baú, flag paused, widget de log |
| `utils/config.py` | Carregar novas config (mouse_movement, click_hold_ms, micro_pause) |
| `resources/config.yml` | Novas seções de humanização |
| `functionality/stash_loop.py` | Incrementar contadores, micro-pausas |
| `gui/gui_initializer.py` | Tamanho inicial maior, tema clam |
| `gui/stash_panel.py` | Contadores na UI, mini log, botão logs, botões coloridos |
| `gui/gui_functions.py` | File logging no stash, resetar contadores, pausa |
| `wrappers/logging_wrapper.py` | Rotação de logs, formato melhorado, prefix stash |

---

## Ordem de implementação recomendada

1. **GUI/Design** — impacto visual imediato, sem risco de quebrar automação
2. **Contadores de baú** — feature nova isolada, fácil de testar
3. **Logging melhorado** — melhora diagnóstico sem alterar fluxo principal
4. **Humanização** — maior risco de regressão; testar cada sub-item separado
5. **Outros ajustes** — pausar, ícone, export/import

## Verificação

- Abrir o app e confirmar que a janela mostra todos os botões sem scroll na abertura
- Iniciar Stash com o jogo aberto → verificar que contadores sobem ao abrir baús
- Verificar que arquivo de log foi criado em `logs/stash_*.log`
- Clicar "Abrir pasta de logs" → Explorer abre na pasta correta
- Em modo DEBUG, verificar nos logs que coordenadas de clique variam entre runs
- Observar no mouse que ele se move gradualmente (não teleporta) ao clicar nos botões
