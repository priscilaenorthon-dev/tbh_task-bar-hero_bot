# TBH Helper — Assistente de Stash para Task Bar Hero

Assistente em Python que automatiza o gerenciamento do stash no Task Bar Hero. Ele encontra os botões na tela e clica automaticamente, dispensando você de fazer isso manualmente o tempo todo.

## Suporte

https://saweria.co/goldiegaming | https://ko-fi.com/alandtiwa

---

## O que o bot faz?

O bot fica rodando em segundo plano enquanto você joga e executa este ciclo automaticamente:

1. **Abre o baú** — clica com o botão direito no ícone de baú (boss ou normal)
2. **Auto Fill** — clica no botão de auto fill e verifica se aparece combine
   - Se aparecer combine: clica em combine → clica em voltar → recomeça do passo 1
   - Se não aparecer: vai direto para o próximo passo
3. **Stash All** — clica para guardar tudo no stash
4. **Fechar** — fecha/volta da tela de stash

Além disso, em paralelo, um **timer em segundo plano** de tempos em tempos clica em Stash All + Sort e pressiona Espaço automaticamente.

---

## Requisitos

- **Windows** (obrigatório — usa API do Windows para os cliques)
- **Python 3.10 ou superior**
- Task Bar Hero aberto e rodando

---

## Instalação (primeira vez)

Abra o terminal na pasta do projeto e execute:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Para iniciar o bot:

```bash
python main.py
```

---

## Configuração inicial (faça isso antes de usar)

Na primeira vez que abrir o bot, você precisa fazer **duas configurações obrigatórias** antes de apertar Iniciar.

### Passo 1 — Defina a região de busca (aba "Tela")

O bot precisa saber **em qual área da tela** ele deve procurar os botões do jogo.

1. Abra o **Task Bar Hero** e deixe visível a interface do stash (aquela parte com os ícones de baú)
2. No bot, clique na aba **Tela**
3. Clique em **"Desenhar região de busca"**
4. A tela vai ficar escurecida — clique e arraste com o **botão esquerdo do mouse** em volta da área do stash no jogo
5. Solte o mouse — a região será salva

> **Dica:** Quanto menor a área desenhada (só o necessário), mais rápido o bot vai encontrar os botões.

Depois de desenhar, clique em **"Visualizar região"** para confirmar que ficou certo. Clique em qualquer lugar para fechar a prévia.

### Passo 2 — Configure a escala de UI (aba "Tela")

Logo abaixo da região de busca, há o campo **"Escala de UI"**. Ele precisa corresponder à escala que você configurou dentro do Task Bar Hero.

| Escala no jogo | Valor a selecionar |
|---|---|
| 100% | `1` |
| 125% | `1.25` |
| 150% | `1.5` |
| 200% | `2` |

Selecione o valor correto na lista. Se errar, o bot não vai encontrar os botões.

---

## Como usar no dia a dia

1. Abra o **Task Bar Hero**
2. Fique perto do seu baú/stash no jogo
3. Abra o bot (`python main.py`)
4. Na aba **Executar**, clique em **"Iniciar Stash"**
5. **Clique na janela do jogo** para ela ficar em foco
6. O bot começa a trabalhar automaticamente

Para parar, clique em **"Parar Stash"** no bot.

> As configurações são salvas automaticamente quando você fechar o bot.

---

## Verificando se está tudo certo (Diagnóstico)

Se o bot não estiver encontrando os botões, use o **Diagnóstico** antes de qualquer coisa:

1. Abra a aba **Executar**
2. Clique em **"Executar diagnóstico"**
3. Veja os resultados:
   - **[OK]** — tudo certo
   - **[AVISO]** — o bot rodou mas não encontrou o template na tela (coloque o jogo visível na região configurada)
   - **[FALHA]** — tem um problema que precisa ser resolvido (região muito pequena, arquivo ausente, etc.)

> O diagnóstico **não clica em nada** — é só uma verificação segura.

---

## Ajustando os tempos (aba "Temporização")

Todos os campos usam **mínimo e máximo** em segundos. O bot escolhe um valor aleatório dentro desse intervalo a cada ação, o que faz ele parecer mais humano.

| Campo | O que faz | Padrão sugerido |
|---|---|---|
| **Repetição do loop** | Tempo entre cada tentativa de encontrar um botão | mín 1.2 / máx 1.8 s |
| **Limite de espera da etapa** | Tempo máximo esperando um botão antes de pular para o próximo | mín 45 / máx 60 s |
| **Pausa após clique** | Pausa depois de cada clique, para a animação do jogo carregar | mín 0.8 / máx 1.4 s |
| **Espera antes do combine** | Quanto tempo esperar após Auto Fill para verificar se apareceu combine | mín 2.5 / máx 3.5 s |
| **Intervalo do ciclo** | De quanto em quanto tempo roda o stash/sort em segundo plano | mín 28 / máx 32 s |
| **Intervalo Stash → Sort** | Pausa entre clicar em Stash All e Sort no ciclo em segundo plano | mín 0.2 / máx 0.6 s |
| **Deslocamento em pixels** | Quanto o clique pode desviar do centro exato do botão (anti-detecção) | mín -8 / máx 8 |

> Não mexa nesses valores sem necessidade. Os padrões funcionam bem para a maioria dos casos.

---

## O que acontece quando o bot não encontra um botão?

O bot **não trava nem fica em loop infinito**. Se um botão não aparecer dentro do tempo configurado em "Limite de espera da etapa", ele pula para a próxima etapa automaticamente. O status na tela vai mostrar `Pulado …, próximo: …`.

| Situação | O que o bot faz |
|---|---|
| Baú não encontrado | Fica tentando até o limite de espera, depois pula |
| Combine não aparece após Auto Fill | Pula direto para Stash All (sem espera longa) |
| Botão de voltar não aparece após combine | Fica tentando até o limite, depois pula para Stash All |
| Stash/Sort do timer de fundo não encontrados | Pula o clique e aguarda o próximo ciclo |

---

## Nível de log (aba "Executar")

Controla quanto detalhe aparece no console:

- **INFO** — recomendado para uso normal (mostra o que o bot está fazendo)
- **DEBUG** — mostra o score de cada template encontrado e coordenadas de clique (útil para diagnosticar problemas)
- **WARNING** / **ERROR** — só erros e avisos

---

## Criando um executável (.exe)

Se quiser um `.exe` para não precisar do Python instalado:

```bash
pip install pyinstaller
pyinstaller --name TBHHelper --add-data "resources;resources" --add-data "assets;assets" main.py
```

O arquivo ficará em `dist/TBHHelper/TBHHelper.exe`.

---

## Problemas comuns

**O bot abre mas não clica em nada**
→ Verifique se a região de busca foi desenhada corretamente (aba Tela → Visualizar região)
→ Execute o Diagnóstico e veja o resultado de cada check

**O bot clica no lugar errado**
→ A escala de UI pode estar errada — confira na aba Tela

**"AVISO" no diagnóstico para todos os templates**
→ O bot não está vendo o jogo na região configurada. Certifique-se de que a janela do jogo está visível e na posição certa

**O bot para sozinho após alguns segundos**
→ O "Limite de espera da etapa" pode estar muito baixo — aumente o valor mínimo e máximo na aba Temporização
