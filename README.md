# TBH Helper — Assistente de Stash para Task Bar Hero

Assistente em Python que automatiza o gerenciamento do stash e a navegação de mapas no Task Bar Hero. Detecta os botões na tela via reconhecimento de imagem e clica automaticamente, liberando você para jogar enquanto o gerenciamento roda em segundo plano.

[![Plataforma](https://img.shields.io/badge/plataforma-Windows-blue)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/python-3.10%2B-yellow)](https://www.python.org/)
[![Licença](https://img.shields.io/badge/licença-pessoal-lightgrey)](#)

## Apoie o projeto

[saweria.co/goldiegaming](https://saweria.co/goldiegaming) | [ko-fi.com/alandtiwa](https://ko-fi.com/alandtiwa)

---

## O que o bot faz?

### Automação de Stash (funcionalidade principal)

O bot roda em segundo plano e executa este ciclo automaticamente enquanto você joga:

1. **Abre o baú** — clica com o botão direito no ícone de baú (boss ou normal)
2. **Auto Fill** — clica no botão de auto fill e verifica se aparece combine
   - Se aparecer combine: clica em combine → clica em voltar → recomeça do passo 1
   - Se não aparecer: vai direto para o próximo passo
3. **Stash All** — clica para guardar tudo no stash
4. **Fechar** — fecha/volta da tela de stash

Em paralelo, um **timer em segundo plano** clica automaticamente em Stash All + Sort e pressiona Espaço de tempos em tempos.

### Caça ao Baú — Map Runner (funcionalidade secundária)

Navegação automática de mapas com seleção de dificuldade e ato. O bot:

- Navega pelo portal de mapas
- Seleciona dificuldade (Normal, Nightmare, Hell, Torment)
- Percorre até 30 mapas diferentes em 3 atos
- Controla o tempo por mapa e o timer de respawn de baús
- Clica automaticamente nos baús encontrados (boss e normal)

---

## Requisitos

- **Windows** (obrigatório — usa API do Windows para cliques e captura de tela)
- **Python 3.10 ou superior**
- Task Bar Hero aberto e rodando

---

## Instalação

Abra o terminal na pasta do projeto e execute:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Para iniciar:

```bash
python main.py
```

Ou clique duas vezes em **`Iniciar TBH Helper.bat`** (Windows).

---

## Configuração inicial

Na primeira vez, faça **duas configurações obrigatórias** antes de clicar em Iniciar.

### Passo 1 — Região de busca (aba "Tela")

O bot precisa saber em qual área da tela procurar os botões do jogo.

1. Abra o Task Bar Hero com a interface do stash visível
2. No bot, clique na aba **Tela**
3. Clique em **"Desenhar região de busca"**
4. A tela escurece — arraste com o botão esquerdo ao redor da área do stash
5. Solte — a região é salva automaticamente

Clique em **"Visualizar região"** para confirmar. Clique em qualquer lugar para fechar a prévia.

> Quanto menor a área (só o necessário), mais rápido o bot encontra os botões.

### Passo 2 — Escala de UI (aba "Tela")

Deve corresponder à escala configurada dentro do Task Bar Hero:

| Escala no jogo | Valor a selecionar |
|---|---|
| 100% | `1` |
| 125% | `1.25` |
| 150% | `1.5` |
| 200% | `2` |

Se errar a escala, o bot não encontra os botões.

---

## Como usar no dia a dia

1. Abra o **Task Bar Hero** e fique perto do stash
2. Abra o bot (`python main.py`)
3. Na aba **Executar**, clique em **"Iniciar Stash"**
4. **Clique na janela do jogo** para ela ficar em foco
5. O bot trabalha automaticamente

Para parar: clique em **"Parar Stash"**.

> As configurações são salvas automaticamente ao fechar o bot.

---

## Ajustando os tempos (aba "Temporização")

Todos os campos usam **mínimo e máximo** em segundos. O bot escolhe um valor aleatório dentro do intervalo a cada ação, tornando o comportamento mais natural.

| Campo | O que faz | Padrão |
|---|---|---|
| **Repetição do loop** | Intervalo entre tentativas de encontrar um botão | 1.2 / 1.8 s |
| **Limite de espera da etapa** | Tempo máximo aguardando um botão antes de pular | 45 / 60 s |
| **Pausa após clique** | Pausa após cada clique (aguarda animação carregar) | 0.8 / 1.4 s |
| **Espera antes do combine** | Tempo após Auto Fill antes de verificar combine | 2.5 / 3.5 s |
| **Intervalo do ciclo** | Intervalo do timer de stash/sort em segundo plano | 28 / 32 s |
| **Intervalo Stash → Sort** | Pausa entre clicar em Stash All e Sort | 0.2 / 0.6 s |
| **Deslocamento em pixels** | Desvio aleatório do clique (anti-detecção) | -8 / +8 px |

> Não altere sem necessidade — os padrões funcionam bem na maioria dos casos.

---

## Diagnóstico

Se o bot não estiver funcionando:

1. Aba **Executar** → clique em **"Executar diagnóstico"**
2. Veja os resultados:
   - **[OK]** — tudo certo
   - **[AVISO]** — template não encontrado na tela (posicione o jogo na região configurada)
   - **[FALHA]** — problema que precisa ser resolvido (região pequena, arquivo ausente, etc.)

> O diagnóstico **não clica em nada** — é uma verificação segura.

---

## O que acontece quando o bot não encontra um botão?

O bot **não trava nem fica em loop infinito**. Se um botão não aparecer dentro do tempo configurado, ele pula para a próxima etapa automaticamente.

| Situação | O que o bot faz |
|---|---|
| Baú não encontrado | Tenta até o limite de espera, depois pula |
| Combine não aparece após Auto Fill | Pula direto para Stash All |
| Botão de voltar não aparece após combine | Tenta até o limite, depois pula para Stash All |
| Stash/Sort do timer de fundo não encontrados | Pula o clique e aguarda o próximo ciclo |

---

## Nível de log (aba "Executar")

| Nível | Quando usar |
|---|---|
| **INFO** | Uso normal — mostra o que o bot está fazendo |
| **DEBUG** | Para diagnosticar — mostra score de templates e coordenadas de clique |
| **WARNING / ERROR** | Só erros e avisos |

---

## Criando um executável (.exe)

```bash
pip install pyinstaller
pyinstaller --name TBHHelper --add-data "resources;resources" --add-data "assets;assets" main.py
```

O executável fica em `dist/TBHHelper/TBHHelper.exe`. O `.exe` deve permanecer na pasta junto com os arquivos gerados.

Para releases automáticas via GitHub Actions, consulte `RELEASES.md`.

---

## Problemas comuns

**O bot abre mas não clica em nada**
→ Verifique a região de busca (aba Tela → Visualizar região)
→ Execute o diagnóstico e analise cada resultado

**O bot clica no lugar errado**
→ A escala de UI provavelmente está incorreta — confira na aba Tela

**"AVISO" para todos os templates no diagnóstico**
→ O jogo não está visível na região configurada — reposicione a janela do jogo

**O bot para sozinho após alguns segundos**
→ O "Limite de espera da etapa" pode estar muito baixo — aumente os valores na aba Temporização

**Erro ao iniciar / módulo não encontrado**
→ Certifique-se de ativar o ambiente virtual (`venv\Scripts\activate`) antes de rodar
