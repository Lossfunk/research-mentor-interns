# Academic Research Mentor

An AI-powered research mentor agent that provides guidance and assistance for academic research tasks. The system uses LangChain and OpenAI to create an intelligent mentor that can help with research planning, methodology, and academic writing.

## How to Run

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Add your OpenAI API key and LangSmith API key (optional) to the `.env` file.
   
   **Note:** If you don't add the LangSmith API key, set tracing to false in the configuration. If things break when tracing is set to false, set it back to true and create an API key at [smith.langchain.com](https://smith.langchain.com).

3. **Run the application:**
   ```bash
   uv run main.py
   ```
