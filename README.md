# Academic Research Mentor

## Objective
Accelerate AI research with AI. We are building an AI Research Mentor that guides researchers through the entire research lifecycle so they can move from idea to published work faster.

## Key Capabilities
- **Research-aware Web UI** powered by direct **OpenAI SDK** integration for transparent and reliable agent behavior.
- **Interactive Research Canvas**: A notebook-centric interface with drag-and-drop support, rich text editing, and infinite whiteboard space.
- **Dynamic Tool Routing**: Smart selection of research tools including web search, arXiv, and guidelines.
- Mentorship guidelines and experiment planning helpers to keep projects on track.

## Setup

### Backend
```bash
# Install Python dependencies
uv sync

# Run tests (optional)
uv run pytest -q
```

### Frontend
```bash
cd web
npm install
```

## Environment
```bash
cp .example.env .env
```
Edit `.env` and add your `OPENROUTER_API_KEY` (recommended). Other provider keys are optional fallbacks.

## Usage

### 1. Start the Backend Server
```bash
uv run python -m uvicorn academic_research_mentor.server:app --reload --port 8000
```

### 2. Start the Frontend Web UI
```bash
cd web
npm run dev
```
The web interface will be available at `http://localhost:3000`.

## How It Works

As you work on your Lossfunk application, you can use the research mentor for the following:

**Brainstorming and discussing a research proposal:** Kick off an idea sprint, explore literature leads, and co-develop an initial plan directly in the interactive canvas.

**Reviewing a finished proposal (with PDF):** Attach the draft so the mentor can critique structure, highlight gaps, and suggest revisions with citations.

# Outdated setup, need to update.
Here is a quick video walkthrough of how this works: https://youtu.be/xupym38Ms4g

[![Watch Demo](https://img.youtube.com/vi/xupym38Ms4g/maxresdefault.jpg)](https://youtu.be/xupym38Ms4g)

*Note: Your application decision will not be impacted in any way by your use or not of this tool.*

## FAQ

1. **Can I use `pip` instead of `uv`?**  
   You can, but we recommend `uv` because it gives fine-grained control over Python versions and dependency resolution, which improves reproducibility. See a deeper comparison here: <https://blog.kusho.ai/uv-pip-killer-or-yet-another-package-manager/>

2. **When running the mentor I see `ModuleNotFoundError: No module named 'academic_research_mentor'`. How do I fix this?**  
   This is usually a path-resolution issue. Add the following to your `pyproject.toml`:
   ```toml
   [tool.setuptools.packages.find]
   where = ["./"]
   include = ["academic-research-mentor"]
   ```
   More background: <https://stackoverflow.com/questions/79340227/modulenotfounderror-when-installing-my-own-project>

3. **Can I attach a PDF?**  
   Yes. In the Web UI, you can drag and drop PDFs directly.

4. **Can I resume past conversations?**  
   Yes. The Web UI persists conversations automatically.

## Troubleshooting
- Ensure Python 3.11+ is installed.
- Re-run `uv sync` after dependency changes.
