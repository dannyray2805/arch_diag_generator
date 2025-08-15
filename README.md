# Heading One Architecture Diagram Generator Tool
This project is an AI-powered tool that generates cloud architecture diagrams from natural language descriptions. It combines a graphical user interface (GUI), a powerful local Large Language Model (LLM) via Ollama, and the popular diagrams Python library to create a seamless text-to-diagram workflow. It has the ability to generate diagrams from Azure, AWS, GCP, On-Premises platform and infratructure as a service architecture diagrams. The output can be both in PNG and SVG formats.

# Code Explanation

This project is an AI-powered tool that generates cloud architecture diagrams from natural language descriptions. It cleverly combines a graphical user interface (GUI), a powerful local Large Language Model (LLM) via Ollama, and the popular diagrams Python library to create a seamless text-to-diagram workflow.

The architecture is split into two main files:

* [prompts.py].(): The "brain" of the operation. It contains the master prompt template used to instruct the LLM.
* diagram_generator_v3_diagrams.py: The main application. It provides the GUI, orchestrates the interaction with the LLM, processes the response, and renders the final diagram.

Key Concepts:

Persona Setting: The prompt begins by telling the LLM to act as "an expert Python developer specialized in creating architecture diagrams." This sets the context and encourages the model to generate high-quality, relevant code.
Strict Rules: A set of "CRITICAL RULES" are provided to constrain the LLM's output. This is vital for ensuring the generated code is directly executable by the main application. It prevents the model from adding conversational text, import statements, or other code that would cause errors.
Few-Shot Learning: The template includes five complete, high-quality examples of diagrams code for various architectures (Azure 3-tier, AWS Landing Zone, etc.). This is a powerful technique that shows the model exactly what a good response looks like, significantly improving the quality and consistency of its output.
Templating: The prompt uses placeholders like {user_input}, {fontsize}, {bgcolor}, and {layout_dir}. The main application replaces these with the user's text and selected style options before sending the final prompt to the LLM.
In essence, this file doesn't execute any logic itself but provides the carefully crafted instructions that make the AI's code generation reliable.

2. diagram_generator_v3_diagrams.py - The Orchestrator
This is the main, executable script that brings everything together. It provides a user-friendly GUI built with Tkinter and manages the entire workflow from user input to final diagram image.

Workflow:

User Input: The user types a description of the desired architecture (e.g., "a 3-tier web app in Azure") into the GUI and selects styling options like layout direction and colors.
Prompt Formatting: The application takes the user's input and style choices and formats the PROMPT_TEMPLATE from prompts.py into a complete prompt.
LLM Code Generation: It sends this detailed prompt to a locally running Ollama LLM (e.g., llama3). The LLM, guided by the prompt, generates Python diagrams code.
Code Extraction & Cleaning: The application receives the raw text from the LLM and intelligently extracts only the Python code block, discarding any surrounding text or markdown fences.
Parameter Injection: It then injects a standard set of import statements (DIAGRAMS_IMPORTS) into the code. Crucially, it uses the _force_diagram_params function to modify the with Diagram(...) line, ensuring the user's GUI style selections (like layout and color) override anything the AI might have generated. It also sets the output filename and format (.svg, .png).
Execution & Rendering: The final, complete Python script is written to a temporary file. The application then executes this script in a separate subprocess. The diagrams library code runs and, using the Graphviz backend, renders the final SVG and PNG image files.
GUI Responsiveness: The entire generation and rendering process runs in a separate thread (GenerationThread) to prevent the GUI from freezing, providing a smooth user experience. A queue is used to pass status updates, results, and errors back to the main GUI thread.
Key Architectural Features:

GUI (gui_main): A user-friendly interface built with Python's standard tkinter library.
LLM Integration (ollama): Communicates with the local LLM service.
Robust Rendering (_run_python_script): Safely executes the generated code in an isolated environment to produce the diagram, capturing any errors for debugging.
Extensive Logging: The application logs detailed information about every step to both the console and diagram_generator.log, which is invaluable for troubleshooting.
