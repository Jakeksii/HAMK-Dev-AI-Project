# Simple Calendar assistant

Simple Calendar assistant for the **Development of AI Applications** course final group project.

## Team members

- Tomi Kitola (email@example.com)
- Jaakko Ruhanen (email@example.com)
- Member 3 Name (email@example.com)

## Problem
Calendar usage is time consuming work, and people are lazy.

### Intended users
Everyday people that are busy in their day to day lives. Especially business people!

### Problem statement
this application entirely removes the manual step of updating users calendar.

### Why AI is appropriate
AI agent improves the the experience of the user. Without AI agent the human would need to update the calendar manually.

## Solution
An AI agent that turns plain text, a quick note, a forwarded email, a voice memo transcript, into calendar events automatically, connecting to Google Calendar via MCP so users never have to manually open their calendar and enter event details themselves.

## Main user workflow

1. **User Input:** The user submits a prompt or query via the Gradio user interface.
2. **Processing & Guardrails:** The application service layer (`src/services/ai_service.py`) validates and formats the request.
3. **Model Response:** The model client calls cloud LLM through local ollama proxy and forwards the response through the tool layer.
4. **MCP call:** Tool call layer parses model output and determines the LLM intent to call a tool.
5. **MCP response:** Tool call layer responses to model with tool call results.
6. **Model Response:** The model client calls LLM through API and returns the response back through the service layer to the UI

## Architecture

Below is the initial starter architecture. As your project evolves with additional capabilities, replace or extend this diagram in [`docs/architecture.md`](docs/architecture.md).

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
Application / AI Service (src/services/ai_service.py)
  ↓
Model Client (src/models/model_client.py)
  ↓
Ollama (Local LLM Server)
```

> **Core Architectural Rule:** The user interface must NEVER communicate directly with the model client or Ollama. All interactions must pass through the service layer (`ai_service.py`).

## Model

- **Model used:** e.g., `Qwen2.5` (or specified local Ollama model)
- **Selection rationale:** `qwen2.5:14b-instruct` balances reliable tool-calling accuracy with local reproducibility, running at Q4 on a single consumer GPU (~10GB VRAM) with no API costs.

## Additional AI capability

Select at least one additional capability to implement for your final project:

- [ ] RAG (Retrieval-Augmented Generation)
- [x] Tools / External API integration
- [x] Model Context Protocol (MCP)
- [ ] Agentic workflow (Model-selected actions based on observations)
- [ ] Memory / Persistent state
- [ ] Multimodal interaction (Text + Images)
- [ ] Other: ______________________

### Capability justification
Tools/MCP integration is essential because the core problem (manual calendar entry) requires the LLM to act. Tool calling lets the model turn parsed intent (e.g., "lunch Thursday at noon") into a real action on Google Calendar. MCP standardizes that connection, decoupling the tool layer from the model client so calendar operations are exposed as clean, discoverable functions rather than hardcoded API logic, keeping the architecture modular and easy to extend.

## Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
```

### 2. Activate the environment

```bash
conda activate dev-ai-project
```

### 3. Configure environment variables

Copy `.env.example` to create your local `.env` configuration file:

On Linux / macOS:
```bash
cp .env.example .env
```

On Windows (Command Prompt / PowerShell):
```powershell
copy .env.example .env
```

Ensure `.env` contains valid values for `OLLAMA_BASE_URL` and `MODEL_NAME`:
```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2.5
```

### 4. Start Ollama

Make sure Ollama is installed and running locally, then pull your configured model:

```bash
ollama run qwen2.5
```

### 5. Run the application

Run the application from the root directory of the project:

```bash
python -m app.main
```

Then open your browser at `http://localhost:7860`.

### 6. Run automated tests

```bash
pytest
```

# Todo: Plan steps below:

## Evaluation

Describe your evaluation methodology and summarize key results. Starter test cases can be found in [`evaluation/test_cases.json`](evaluation/test_cases.json).

Refer to [`evaluation/README.md`](evaluation/README.md) for guidelines on defining success, edge cases, and failure scenarios.

## Known limitations

- Highlight known system limitations, unhandled edge cases, or boundaries of current capabilities.

## Future improvements

- List planned feature enhancements, architectural refactorings, or future capabilities.
