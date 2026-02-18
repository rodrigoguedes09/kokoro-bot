# Kokoro Bot — The Vibe Architect 🎧

> **Missão:** Ouvir áudios do mundo real e revelar a "Informação Mágica" que as pessoas não percebem — sentimentos ocultos, tensões não ditas, tópicos ignorados e ações pendentes.

---

## 1. Visão Geral

O Kokoro Bot é uma ferramenta de **análise de áudio inteligente** que usa as APIs de Audio Intelligence da **Deepgram** (Speech-to-Text, Sentiment Analysis, Intent Recognition, Topic Detection e Summarization) para transformar conversas faladas em insights acionáveis.

### Modos de Operação

| Modo | Descrição |
|------|-----------|
| **CLI (Standalone)** | Analisa arquivos de áudio locais ou URLs e gera um Vibe Report no terminal/arquivo. |
| **Discord Bot** | Entra em canais de voz, grava a reunião e posta um Vibe Report visual no canal de texto. |

---

## 2. O que ele Analisa (Os Insights "Mágicos")

Usando as 4 features de Audio Intelligence da Deepgram, o bot extrai dados que vão muito além das palavras:

### 2.1 Sentiment Timeline (Sentiment Analysis)
- **Picos de Tensão:** Identifica o momento exato em que o sentimento mudou de "Neutro/Positivo" para "Negativo".
  - *Exemplo:* "Aos 14:20, houve uma queda de 40% no sentimento quando o assunto 'Prazo' foi mencionado."
- **Vibe Score Geral:** Média ponderada do sentimento da conversa inteira (-1 a +1).

### 2.2 Detecção de Intenção (Intent Recognition)
- **Nível de Consenso:** Detecta se as pessoas estavam concordando (`Affirmation`) ou questionando (`Disagreement`).
- **Action Items:** Identifica intenções de ação ("vou fazer", "preciso entregar", "fica combinado").

### 2.3 Tópicos Chave (Topic Detection)
- **O "Elefante na Sala":** Tópicos mencionados brevemente mas que geraram hesitação ou sentimento negativo.
- **Mapa de Tópicos:** Lista dos assuntos tratados com relevância e sentimento associado.

### 2.4 Resumo Inteligente (Summarization)
- **TL;DR Automático:** Resumo conciso da conversa inteira gerado pela Deepgram.

### 2.5 Insights Derivados (Analytics Engine)

| Insight | O que a IA Detectou | O que o Usuário Lê |
|---------|---------------------|---------------------|
| **Vibe Shift** | Mudança súbita de sentimento entre segmentos consecutivos. | "O clima esquentou aos 10min quando 'Deploy' surgiu — sentimento caiu de +0.6 para -0.4." |
| **Tópico Quente** | Tópico com o sentimento mais negativo ou controverso. | "O assunto 'Orçamento' gerou o sentimento mais negativo da reunião (-0.7)." |
| **Consenso vs. Conflito** | Proporção de intenções de concordância vs. discordância. | "70% das intenções foram de concordância. Nível de alinhamento: Alto." |

---

## 3. Arquitetura Técnica

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Audio Source    │────▶│  Deepgram API    │────▶│  Analytics Engine   │
│                 │     │                  │     │                     │
│ • Local file    │     │ • STT (nova-3)   │     │ • Sentiment timeline│
│ • URL           │     │ • sentiment=true │     │ • Vibe shifts       │
│ • Discord voice │     │ • intents=true   │     │ • Topic heat map    │
│                 │     │ • topics=true    │     │ • Consensus score   │
│                 │     │ • summarize=v2   │     │ • Action items      │
└─────────────────┘     └──────────────────┘     └────────┬────────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────────┐
                                                │  Report Generator   │
                                                │                     │
                                                │ • Terminal output   │
                                                │ • Sentiment chart   │
                                                │ • Discord embed     │
                                                │ • JSON export       │
                                                └─────────────────────┘
```

### Stack Tecnológico

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.11+ |
| STT & AI | Deepgram SDK (`deepgram-sdk`) |
| Discord | `discord.py` |
| Gráficos | `matplotlib` |
| Config | `python-dotenv` / `pydantic-settings` |
| CLI | `argparse` |

---

## 4. Estrutura do Projeto

```
kokoro-bot/
├── src/
│   └── kokoro/
│       ├── __init__.py
│       ├── __main__.py          # Entry point CLI
│       ├── config.py             # Settings (API keys, thresholds)
│       ├── models.py             # Dataclasses de dados
│       ├── deepgram_client.py    # Wrapper da API Deepgram
│       ├── analyzer.py           # Analytics Engine (insights mágicos)
│       ├── report.py             # Gerador de relatórios (texto + gráfico)
│       ├── discord_bot.py        # Bot Discord
│       └── utils.py              # Helpers
├── tests/
│   ├── __init__.py
│   └── test_analyzer.py
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── README.md
└── context.md
```

---

## 5. Parâmetros Deepgram Utilizados

```python
options = {
    "model": "nova-3",
    "language": "en",          # Audio Intelligence suporta apenas inglês
    "sentiment": True,         # Sentiment Analysis por segmento e palavra
    "intents": True,           # Intent Recognition
    "topics": True,            # Topic Detection
    "summarize": "v2",         # Summarization automática
    "smart_format": True,      # Pontuação e formatação inteligente
    "diarize": True,           # Separação por falante
}
```

> ⚠️ **Limitação:** Audio Intelligence features funcionam apenas para transcrições em **inglês** e têm limite de **150K tokens** de input.

---

## 6. Output: O Vibe Report

O relatório final inclui:

1. **📝 Resumo (TL;DR)** — Gerado pela Deepgram Summarization.
2. **📊 Sentiment Timeline** — Gráfico mostrando a evolução do sentimento ao longo do áudio.
3. **🔥 Vibe Shifts** — Momentos onde o sentimento mudou drasticamente.
4. **🎯 Tópicos Principais** — Lista de tópicos detectados com sentimento associado.
5. **🤝 Índice de Consenso** — Proporção de concordância vs. discordância nas intenções.
6. **⚡ Action Items** — Intenções de ação detectadas na conversa.

