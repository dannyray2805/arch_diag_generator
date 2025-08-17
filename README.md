# Architecture Diagrams Generator using LLM and Python Diagrams Library

## Key Features

- **AI-Powered Diagram Generation**: Leverages a local LLM (e.g., `llama3`) to convert architecture descriptions into Python code using the `diagrams` library.
- **Enhanced GUI**: Built with `tkinter`, offering an intuitive interface for user interaction.
- **Customizable Diagrams**: Supports customization of layout, font size, background color, and output format.
- **Extensive Cloud Provider Support**: Includes pre-defined nodes for AWS, Azure, GCP, and more.
- **Error Handling**: Comprehensive error management for seamless operation.
- **Progress Display**: Provides real-time progress updates during diagram generation.
- **Multi-Format Output**: Generates diagrams in both SVG and PNG formats.

---

## Technology Stack and Versions

| Technology                           | Version       |
|-------------------------------------|---------------|
| 🐍 Python                            | 3.9+          |
| 🖼️ Diagrams Library                  | Latest        |
| 🧠 Ollama (Local LLM Engine)         | Llama3        |
| 🖥️ Tkinter (GUI Framework)           | Built-in      |
| 📦 Tempfile (Temporary File Handling)| Standard      |
| 🪵 Logging (Debugging & Monitoring)  | Standard      |


## How it Works

The application follows a simple yet powerful workflow:

1. **User Input**: The user types a description of the desired architecture (e.g., "a 3-tier web app in Azure") into the GUI and selects styling options.
2. **AI Code Generation**: The description is sent to a local LLM (like Llama 3), which is guided by a sophisticated prompt to generate Python code using the `diagrams` library.
3. **Code Execution**: The application safely executes the generated Python code in a separate process.
4. **Diagram Rendering**: The `diagrams` library, powered by Graphviz, renders the architecture into high-quality SVG and PNG image files.
5. **Display**: The final diagram is automatically opened for viewing.

## Setup and Usage

1. **Prerequisites**

    - Python 3.9+
    - Graphviz: The `diagrams` library requires Graphviz to be installed and for the dot command to be in your system's PATH. You can download it from [Download](graphviz.org/download).
    - Ollama: You need to have the Ollama service running locally. Download it from ollama.com.

2. **Installation**

   ```bash
       # Clone the repository
       git clone <your-repo-url>
       cd <your-repo-directory>
       # Create and activate a virtual environment
       python -m venv venv
       source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
       # Install the required Python packages
       pip install -r requirements.txt
   ```

3. **Ollama Setup**

    - Pull a model that is good at code generation. Llama 3 is recommended.

      ```bash
      ollama pull llama3
      ```

    - Ensure the Ollama application is running in the background.

4. **Running the application**

   ```bash
        python diagram_generator_v3_diagrams.py
   ```

## Behind the Scenes

This project is an AI-powered tool that generates cloud architecture diagrams from natural language descriptions. It cleverly combines a graphical user interface (GUI), a powerful local Large Language Model (LLM) via Ollama, and the popular `diagrams` Python library to create a seamless text-to-diagram workflow. The architecture is split into two main files:

1. **`prompts.py`**: The "brain" of the operation. It contains the master prompt template used to instruct the LLM.
2. **`diagram_generator_v3_diagrams.py`**: The main application. It provides the GUI, orchestrates the interaction with the LLM, processes the response, and renders the final diagram.

### 1. `prompts.py` - The AI's Instruction Manual

This file is a perfect example of advanced prompt engineering. Its sole purpose is to define a highly-detailed, rule-based prompt template (`PROMPT_TEMPLATE`) that guides the LLM to produce valid and consistent Python code for the diagrams library.
Key Concepts:

- **Persona Setting**: The prompt begins by telling the LLM to act as "an expert Python developer specialized in creating architecture diagrams." This sets the context and encourages the model to generate high-quality, relevant code.
- **Strict Rules**: A set of "CRITICAL RULES" are provided to constrain the LLM's output. This is vital for ensuring the generated code is directly executable by the main application. It prevents the model from adding conversational text, `import` statements, or other code that would cause errors.
- **Few-Shot Learning**: The template includes five complete, high-quality examples of `diagrams` code for various architectures (Azure 3-tier, AWS Landing Zone, etc.). This is a powerful technique that shows the model exactly what a good response looks like, significantly improving the quality and consistency of its output.
- **Templating**: The prompt uses placeholders like `{user_input}`, `{fontsize}`, `{bgcolor}`, and `{layout_dir}`. The main application replaces these with the user's text and selected style options before sending the final prompt to the LLM.
In essence, this file doesn't execute any logic itself but provides the carefully crafted instructions that make the AI's code generation reliable.

### 2. `diagram_generator_v3_diagrams.py` - The Orchestrator

This is the main, executable script that brings everything together. It provides a user-friendly GUI built with Tkinter and manages the entire workflow from user input to final diagram image.

- **GUI (`gui_main`)**: A user-friendly interface built with Python's standard `tkinter` library. It allows users to enter text, select styling options, and trigger the generation process.
- **LLM Integration (`generate_diagrams_code`)**: Communicates with the local Ollama LLM service, sending the formatted prompt and receiving the generated code.
- **Code Processing (`_force_diagram_params`)**: Intelligently extracts the Python code from the LLM's response, injects necessary `import` statements, and most importantly, modifies the `with Diagram(...)` call to enforce the user's styling choices from the GUI. This ensures the final output matches the user's expectations.
- **Robust Rendering (`_run_python_script`)**: Safely executes the generated code in an isolated subprocess to produce the diagram. This prevents any errors in the AI-generated code from crashing the main application and allows for capturing detailed error messages for debugging.
- **Multithreading**: The entire generation and rendering process runs in a separate thread (`GenerationThread`) to prevent the GUI from freezing, providing a smooth user experience. A queue is used to pass status updates, results, and errors back to the main GUI thread.
