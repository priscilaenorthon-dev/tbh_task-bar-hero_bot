# TBH (Task Bar Hero) Helper

Assistente em Python que encontra templates de interface na tela e clica neles.

## Suporte

https://saweria.co/goldiegaming | https://ko-fi.com/alandtiwa

## Requisitos

- Windows
- Python 3.10+

## Configuração

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Como usar

1. Abra o jogo e fique perto do seu stash.
2. Na aba **Tela** da interface, configure a **Escala de UI** para corresponder ao TBH (1, 1.25, 1.5 ou 2), depois clique em **Desenhar região de busca** e arraste sobre a interface do seu stash.
3. Ajuste as abas **Temporização** e **Templates** conforme necessário (cada campo tem uma explicação curta).
4. Na aba **Executar**, escolha o nível de log e clique em **Iniciar Stash**, depois foque na janela do jogo.

O app percorre estas etapas em loop:

1. Abrir baú — clica com o botão direito no ícone de baú boss ou normal (boss verificado primeiro)
2. Auto Fill — aguarda um intervalo **aleatório**, depois verifica combine
   - **Se combine aparecer:** clica em combine → voltar → reinicia da etapa 1
   - **Se não aparecer:** continua para Stash All
3. Stash All
4. Fechar/voltar

Durante a execução, um **timer em segundo plano** (intervalo aleatório) tenta Stash All → Sort com um intervalo aleatório entre os cliques, depois pressiona Espaço.

### Prevenção de travamento / UI ausente

Se um ícone de baú ou botão de etapa não for encontrado, o assistente **tenta novamente** no intervalo de sondagem do loop (Temporização → **Repetição do loop**) até que o **Limite de espera da etapa** expire (padrão de cerca de 45–60 segundos, aleatório no intervalo). Então **pula para a próxima etapa** em vez de aguardar indefinidamente ou reiniciar todo o loop.

| Situação | Comportamento |
|----------|---------------|
| Baú ou botão de etapa ausente (após limite de espera da etapa) | Pula para a próxima etapa da lista |
| Prompt de combine ausente após Auto Fill | Avança para Stash All (uma verificação, sem longa espera) |
| `back_arrow` ausente após combine (após limite de espera da etapa) | Pula para Stash All |
| Fluxo de combine concluído (combine + voltar encontrados) | Reinicia a partir de abrir baú |
| Botões de stash/sort periódico ausentes | Pula esse clique no ciclo; continua no próximo intervalo |

O texto de status e os logs mostram `Pulado …, próximo: …` quando uma etapa é pulada.

### Aleatorização anti-detecção

Todos os atrasos e posições de clique usam **intervalos mín/máx** configurados na interface (aba Temporização):

- Sondagens enquanto aguarda UI (**Repetição do loop**)
- Tempo máximo para aguardar um botão ou ícone de baú (**Limite de espera da etapa**)
- Pausa após cliques bem-sucedidos ou após pular uma etapa
- Espera pela verificação de combine após Auto Fill
- Intervalo do ciclo de stash/sort periódico e intervalo stash→sort
- Deslocamento de pixel a partir do centro do template em cada clique

Intervalos mais amplos parecem mais humanos, mas deixam o loop levemente mais lento. Um limite de espera de etapa menor recupera mais rápido quando a UI está errada ou o estado do jogo mudou; um limite maior evita pular durante animações lentas.

## Configuração

Todas as configurações são editadas na interface e salvas em `resources/config.yml` quando você fecha o app. Os nomes dos templates são **nomes base** (ex.: `auto_fill.png`); assets escalados usam sufixos `_1-25`, `_1-50` ou `_2` dependendo da escala da janela.

## Arquitetura

Referência para desenvolvedores sobre a **máquina de estados** do stash (etapas, ramificação combine, pular/reiniciar) e o **comparador de templates** (captura, OpenCV, resolução de escala):

**[docs/automation.md](docs/automation.md)**

## Criando um executável

Veja **[RELEASES.md](RELEASES.md)** para builds locais com PyInstaller e publicação de releases no GitHub.

Build local rápido:

```bash
pip install pyinstaller
pyinstaller --name TBHHelper --add-data "resources;resources" --add-data "assets;assets" main.py
```

Saída: `dist/TBHHelper/TBHHelper.exe`

## Imagens de template

Coloque os PNGs dos templates em `assets/`. Capture recortes pequenos e únicos na mesma resolução e escala em que você joga.
