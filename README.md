# Architecture Diagram Generator Tool

This project is an AI-powered tool that generates cloud architecture diagrams from natural language descriptions. It combines a graphical user interface (GUI) with a powerful local Large Language Model (LLM).

## Code Explanation

This project is divided into two main components:

### 1. [prompts.py](https://github.com/dannyray2805/arch_diag_generator/blob/main/prompts.py) - The Brain
- **Purpose**: Contains the master prompt template used to instruct the LLM.
- **Key Concepts**:
  - **Persona Setting**: Sets context by instructing the LLM to act as "an expert Python developer specialized in creating architecture diagrams."
  - **Strict Rules**: Provides "CRITICAL RULES" to constrain the LLM's output, ensuring the generated code is executable.
  - **Few-Shot Learning**: Includes five high-quality examples (e.g., Azure 3-tier, AWS Landing Zone) for better code generation.
  - **Templating**: Utilizes placeholders like `{user_input}`, `{fontsize}`, `{bgcolor}`, and `{layout_dir}` for user customization.

> **Note**: This file doesn't execute logic but provides instructions for reliable AI code generation.

### 2. [diagram_generator_v3_diagrams.py](https://github.com/dannyray2805/arch_diag_generator/blob/main/diagram_generator_v3_diagrams.py) - The Orchestrator
- **Purpose**: The main executable script offering a user-friendly GUI and managing the entire workflow.
- **Workflow**:
  1. **User Input**: Accepts architecture descriptions and style preferences via the GUI.
  2. **Prompt Formatting**: Formats the user's input into a complete prompt using `PROMPT_TEMPLATE` from `prompts.py`.
  3. **LLM Code Generation**: Sends the prompt to a locally running LLM (e.g., llama3) to generate Python diagrams code.
  4. **Code Extraction & Cleaning**: Extracts Python code blocks from the LLM output while discarding unnecessary text.
  5. **Parameter Injection**: Adds import statements (`DIAGRAMS_IMPORTS`) and modifies the `with Diagram(...)` line using `_force_diagram_params`.
  6. **Execution & Rendering**: Executes the Python script, rendering the diagram using `diagrams` library.
  7. **GUI Responsiveness**: Runs the process in a separate thread for a smooth user experience.
- **Key Features**:
  - **GUI**: Built with `tkinter` for user-friendly interaction.
  - **LLM Integration**: Communicates with a local LLM service.
  - **Robust Rendering**: Safely executes generated code in an isolated environment.
  - **Extensive Logging**: Logs every step for troubleshooting.