
import ollama
import subprocess
import os
import tempfile
import platform
import logging
import time
import re
import queue
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sys
from threading import Thread

# Configure logging to be verbose, outputting to both console and a file
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum verbosity
    format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s',
    handlers=[
        logging.FileHandler("diagram_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---
DEFAULT_OUTPUT_DIR = 'diagrams'
OLLAMA_MODEL = 'llama3'

# --- Diagrams-wide import block to inject into generated code ---
# This provides popular providers & nodes so model output can be minimal.
DIAGRAMS_IMPORTS = r"""
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.generic.os import Windows, LinuxGeneral, Centos, Ubuntu, RedHat
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.generic.network import Router, Switch, Firewall, VPN, Subnet
from diagrams.generic.storage import Storage

# AWS
from diagrams.aws.general import InternetAlt1 as AWSInternet
from diagrams.aws.compute import EC2, EC2Instance, Lambda, ECS, EKS, Batch, ElasticBeanstalk
from diagrams.aws.database import RDS, Dynamodb, ElastiCache, Redshift
from diagrams.aws.storage import S3, EFS, FSx, S3Glacier
from diagrams.aws.network import ELB, ALB, NLB, APIGateway, Route53, VPC, CloudFront, PrivateSubnet, PublicSubnet, TransitGateway, VpnGateway, VPC, VPCPeering, SiteToSiteVpn, DirectConnect, InternetGateway, NATGateway, VpnConnection
from diagrams.aws.analytics import Kinesis, EMR, Glue, Athena
from diagrams.aws.integration import SQS, SNS, Eventbridge
from diagrams.aws.security import IAM, WAF, Cognito, KMS, CloudHSM
from diagrams.aws.management import Cloudwatch, Cloudtrail, SystemsManager

# Azure
from diagrams.azure.compute import FunctionApps, AppServices, KubernetesServices, VMClassic, VMImages, VMLinux, VMScaleSet, VMSS, VMWindows, VM, BatchAccounts
from diagrams.azure.database import SQLDatabases, CosmosDb, DatabaseForPostgresqlServers, DatabaseForMysqlServers
from diagrams.azure.network import LoadBalancers, VirtualNetworks, ApplicationGateway, DNSPrivateZones, DNSZones
from diagrams.azure.storage import BlobStorage, DataLakeStorage, StorageAccounts, QueuesStorage
from diagrams.azure.analytics import Databricks, SynapseAnalytics
from diagrams.azure.integration import ServiceBus, EventGridDomains, EventGridSubscriptions, EventGridTopics
from diagrams.azure.security import KeyVaults, ApplicationSecurityGroups, ConditionalAccess, Defender, ExtendedSecurityUpdates, SecurityCenter, Sentinel
from diagrams.azure.identity import AccessReview, ActiveDirectoryConnectHealth, ActiveDirectory, ADB2C, ADDomainServices, ADIdentityProtection, ADPrivilegedIdentityManagement, AppRegistrations, ConditionalAccess, EnterpriseApplications, Groups, IdentityGovernance, InformationProtection, ManagedIdentities, Users

# GCP
from diagrams.gcp.compute import ComputeEngine, Functions, KubernetesEngine, AppEngine, Run
from diagrams.gcp.database import SQL as GCPSQL, Bigtable, Spanner, Memorystore
from diagrams.gcp.storage import Storage as GCPStorage, Filestore
from diagrams.gcp.network import LoadBalancing, DNS as GCPDNS, VPC as GCPVPC, CDN
from diagrams.gcp.analytics import BigQuery, Dataflow, PubSub

# On-Prem / Generic

from diagrams.onprem.compute import Server, Nomad
from diagrams.onprem.client import Client, Users, User
from diagrams.onprem.monitoring import Nagios, Grafana, PrometheusOperator, Dynatrace, Splunk
from diagrams.onprem.logging import Fluentbit, Graylog, Rsyslog
from diagrams.onprem.security import Vault
from diagrams.onprem.storage import Portworx, Ceph, CephOsd, Glusterfs
from diagrams.onprem.iac import Terraform, Ansible, Awx, Puppet
from diagrams.onprem.ci import Jenkins, GitlabCI, GithubActions

from diagrams.onprem.queue import RabbitMQ, Kafka
from diagrams.onprem.gitops import Flux, ArgoCD
from diagrams.onprem.database import PostgreSQL, MySQL, Cassandra
from diagrams.onprem.network import Nginx, Apache, Internet, Haproxy

# Containers & K8s
from diagrams.k8s.compute import Pod, Deployment, StatefulSet, DaemonSet
from diagrams.k8s.network import Service, Ingress, NetworkPolicy
from diagrams.k8s.storage import PV, PVC
from diagrams.k8s.clusterconfig import HPA
"""

# Import the template from the separate file
from prompts import PROMPT_TEMPLATE

def generate_diagrams_code(user_input):
    """
    Uses an Ollama model to generate Python code that uses the diagrams library.
    """
    logger.info(f"Generating diagrams Python code for: '{user_input[:70]}...'")
    start_time = time.time()
    prompt = PROMPT_TEMPLATE.format(user_input=user_input, fontsize=10, bgcolor="transparent", layout_dir="LR")
    try:
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        raw_response = response['response'].strip()
        logger.debug(f"Raw Ollama response:\\n{raw_response}")

        # Extract Python code, removing markdown fences and other text.
        # It might be inside ```python ... ``` or just ``` ... ```.
        code_match = re.search(r"```(?:python)?\n(.*?)\n```", raw_response, re.DOTALL)
        if code_match:
            py_code = code_match.group(1).strip()
            logger.debug(f"Extracted code from markdown block:\\n{py_code}")
        else:
            # If no markdown fences, find the start of the 'with Diagram' block
            # and discard any text before it. This handles cases where the model
            # just returns code with some introductory text.
            diagram_match = re.search(r"with Diagram", raw_response)
            if diagram_match:
                py_code = raw_response[diagram_match.start():].strip()
                logger.debug(f"Extracted code by finding 'with Diagram':\\n{py_code}")
            else:
                # If all else fails, use the raw response and hope for the best.
                py_code = raw_response

        if "with Diagram" not in py_code:
            raise ValueError("Generated code does not appear to contain a 'with Diagram(...)' block.")
        if "from diagrams" in py_code:
            # We control imports; strip any model-provided imports to avoid conflicts
            logger.debug("Stripping model-provided imports from generated code.")
            lines = [ln for ln in py_code.splitlines() if not ln.strip().startswith("from diagrams")]
            py_code = "\n".join(lines)

        logger.info(f"Diagrams code generation completed in {time.time() - start_time:.2f} seconds.")
        return py_code
    except Exception as e:
        logging.error(f"Failed to communicate with Ollama model: {str(e)}")
        raise

def _force_diagram_params(py_code: str, title: str, filename_base: str, outformat: str,
                          font_size: int = 10, bgcolor: str = "transparent", layout_dir: str = "LR") -> str:
    """
    Ensure the first 'with Diagram(' call includes:
      - show=False
      - outformat
      - filename
      - rankdir in graph_attr
      - font size & background color in graph_attr
    GUI-selected settings override whatever the AI generated.
    """
    code = py_code.replace(';', '')

    # Locate Diagram(...) header
    pattern = re.compile(r'(with\s+Diagram\s*\(.*\)\s*:)')
    match = pattern.search(code)
    if not match:
        raise ValueError("Could not find a Diagram context to modify.")
    header = match.group(1)

    args_pattern = re.compile(r'with\s+Diagram\s*\((.*)\)\s*:')
    args_match = args_pattern.search(header)
    if not args_match:
        raise ValueError("Could not parse Diagram(...) arguments.")
    original_args = args_match.group(1)

    # Ensure a title is present
    if not original_args.strip():
        new_args = f'"{title}"'
    else:
        new_args = original_args

    # Remove conflicting kwargs
    def _strip_kw(argstr, kw):
        return re.sub(rf'\b{kw}\s*=\s*[^,)]+\s*,?', '', argstr)

    for kw in ["outformat", "filename", "show"]:
        new_args = _strip_kw(new_args, kw)

    # Clean commas
    new_args = re.sub(r',\s*,', ',', new_args).strip().strip(',')

    # Merge GUI-selected settings into graph_attr
    graph_attr_str = f'"fontsize": "{font_size}", "bgcolor": "{bgcolor}", "rankdir": "{layout_dir}"'

    if "graph_attr" in new_args:
        # Replace or merge existing
        new_args = re.sub(
            r'graph_attr\s*=\s*\{([^}]*)\}',
            lambda m: f'graph_attr={{ {m.group(1).strip()}, {graph_attr_str} }}',
            new_args
        )
    else:
        # No graph_attr — add it
        new_args += f', graph_attr={{ {graph_attr_str} }}'

    # Enforce filename & output format
    safe_filename_base = filename_base.replace(os.sep, '/')
    enforced = f'{new_args}, show=False, outformat="{outformat}", filename="{safe_filename_base}"'

    new_header = re.sub(r'\(.*\)', f'({enforced})', header, count=1)
    modified_code = code.replace(header, new_header, 1)
    return modified_code

def _wrap_with_injected_imports(py_code: str) -> str:
    return DIAGRAMS_IMPORTS + "\n\n" + py_code

def _run_python_script(code_str: str, workdir: str):
    """Run provided Python code in a temp file."""
    temp_script_filename = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py', encoding='utf-8', dir=workdir) as temp_script:
            temp_script.write(code_str)
            temp_script_filename = temp_script.name

        logger.debug(f"Executing diagrams script: {temp_script_filename}")
        result = subprocess.run(
            [sys.executable, temp_script_filename],
            check=True,
            capture_output=True,
            text=True,
            cwd=workdir
        )
        if result.stderr:
            logger.warning(f"Diagrams script stderr:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Diagrams script failed with exit code {e.returncode}.")
        logger.error(f"--- Failing Python Code ---\n{code_str}\n--------------------------")
        logger.error(f"stderr: {e.stderr}")
        # Re-raise with a more informative message for the user
        raise RuntimeError(f"The generated Python code failed to execute.\n\nError:\n{e.stderr}") from e
    finally:
        if temp_script_filename and os.path.exists(temp_script_filename):
            os.remove(temp_script_filename)

def open_file(filepath):
    """Opens a file in the default application."""
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', filepath], check=False)
        elif platform.system() == 'Windows':  # Windows
            os.startfile(filepath)  # type: ignore[attr-defined]
        else:  # Linux
            subprocess.run(['xdg-open', filepath], check=False)
    except Exception as e:
        logger.debug(f"Could not auto-open the file: {e}")


class ProgressDisplay(ttk.Frame):
    """A custom widget to display detailed progress of the diagram generation."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.columnconfigure(1, weight=1)

        self.step_label = ttk.Label(self, text="Ready.", anchor="w", font=("Segoe UI", 10, "bold"))
        self.step_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2))

        self.progress_bar = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)

        self.details_label = ttk.Label(self, text="", anchor="w", font=("Segoe UI", 8))
        self.details_label.grid(row=2, column=0, sticky="w")

        self.time_label = ttk.Label(self, text="", anchor="e", font=("Segoe UI", 8))
        self.time_label.grid(row=2, column=1, sticky="e")

    def start(self, total_steps):
        self.step_label.config(text="Starting generation...", foreground="black")
        self.progress_bar.config(value=0)
        self.details_label.config(text=f"0% [0/{total_steps}]")
        self.time_label.config(text="Elapsed: 00:00 | ETA: --:--")
        self.progress_bar.start(10) # Gentle pulse effect

    def update(self, step_name, current_step, total_steps, elapsed, eta):
        self.progress_bar.stop()
        self.step_label.config(text=f"{step_name}", foreground="black")
        
        percentage = (current_step / total_steps) * 100
        self.progress_bar.config(value=percentage)
        self.details_label.config(text=f"{int(percentage)}% [{current_step}/{total_steps}]")

        elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
        eta_str = "--:--" if eta is None or eta == float('inf') else time.strftime('%M:%S', time.gmtime(eta))
        self.time_label.config(text=f"Elapsed: {elapsed_str} | ETA: {eta_str}")
def render_diagram(py_code: str, output_base: str, *, font_size_var, bg_color_var, layout_var):
    """Renders both PNG and SVG versions of the diagram."""
    for fmt in ['png', 'svg']:
        code_with_params = _force_diagram_params(
            py_code,
            title=os.path.basename(output_base),
            filename_base=output_base,
            outformat=fmt,
            font_size=font_size_var.get(),
            bgcolor=bg_color_var.get(),
            layout_dir=layout_var.get()
        )
        code_with_params = _wrap_with_injected_imports(code_with_params)
        _run_python_script(code_with_params, workdir=os.path.dirname(output_base))

def gui_main():
    import tkinter as tk
    from tkinter import ttk, messagebox, colorchooser
    from tkinter.scrolledtext import ScrolledText
    import queue
    from threading import Thread

    root = tk.Tk()
    root.title("AI Architecture Diagram Generator")
    root.geometry("800x600")
    style = ttk.Style(root)
    style.theme_use("clam")

    progress_queue = queue.Queue()

    # --- Input Section ---
    input_frame = ttk.LabelFrame(root, text="Architecture Description", padding=10)
    input_frame.pack(fill="both", expand=True, padx=10, pady=10)

    txt_input = ScrolledText(input_frame, wrap="word", height=8, font=("Segoe UI", 10))
    txt_input.pack(fill="both", expand=True)

    # --- Options Section ---
    options_frame = ttk.LabelFrame(root, text="Diagram Options", padding=10)
    options_frame.pack(fill="x", padx=10, pady=5)

    LAYOUT_OPTIONS = ["LR", "TB", "BT", "RL"]
    OUTPUT_FORMATS = ["Both", "PNG", "SVG"]

    ttk.Label(options_frame, text="Layout Direction:").grid(row=0, column=0, sticky="w", pady=5)
    layout_var = tk.StringVar(value="LR")
    layout_combo = ttk.Combobox(options_frame, textvariable=layout_var, values=LAYOUT_OPTIONS, width=5, state="readonly")
    layout_combo.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(options_frame, text="Output Format:").grid(row=0, column=2, sticky="w", pady=5)
    format_var = tk.StringVar(value="Both")
    format_combo = ttk.Combobox(options_frame, textvariable=format_var, values=OUTPUT_FORMATS, width=8, state="readonly")
    format_combo.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(options_frame, text="Font Size:").grid(row=0, column=4, sticky="w", pady=5)
    font_size_var = tk.IntVar(value=10)
    font_slider = ttk.Scale(options_frame, from_=8, to=20, orient="horizontal", variable=font_size_var)
    font_slider.grid(row=0, column=5, padx=5, pady=5)

    ttk.Label(options_frame, text="Background:").grid(row=0, column=6, sticky="w", pady=5)
    bg_color_var = tk.StringVar(value="transparent")
    def choose_color():
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[1]:
            bg_color_var.set(color[1])
    bg_button = ttk.Button(options_frame, text="Pick", command=choose_color)
    bg_button.grid(row=0, column=7, padx=5, pady=5)

    # --- Status and Progress ---
    status_frame = ttk.Frame(root, padding=10)
    status_frame.pack(fill="x")

    status_label = ttk.Label(status_frame, text="", wraplength=600)
    status_label.pack(anchor="w")

    progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
    progress_bar.pack(fill="x", pady=5)

    # --- Action Buttons ---
    button_frame = ttk.Frame(root, padding=10)
    button_frame.pack(fill="x")

    def process_queue():
        try:
            while True:
                msg_type, msg_payload = progress_queue.get_nowait()
                if msg_type == 'status':
                    status_label.config(text=msg_payload)
                elif msg_type == 'success':
                    status_label.config(text=f"✅ Diagram saved to {msg_payload}.svg / .png")
                    progress_bar.stop()
                elif msg_type == 'error':
                    messagebox.showerror("Error", msg_payload)
                    progress_bar.stop()
                elif msg_type == 'done':
                    generate_button.config(state=tk.NORMAL)
                    progress_bar.stop()
        except queue.Empty:
            pass
        finally:
            root.after(100, process_queue)

    def generate_task():
        user_input = txt_input.get("1.0", tk.END).strip()
        if not user_input:
            progress_queue.put(('error', "No input provided."))
            progress_queue.put(('done', None))
            return

        progress_queue.put(('status', "Generating diagram... Please wait."))
        progress_bar.start()

        try:
            # Pass parameters into the AI prompt
            prompt_with_style = f"{user_input} (Layout: {layout_var.get()}, Font size: {font_size_var.get()}, Background: {bg_color_var.get()})"
            py_code = generate_diagrams_code(prompt_with_style)

            # Adjust output filename
            sanitized_input = re.sub(r'[^\w_]+', '_', user_input.lower())[:50].strip('_')
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_base = os.path.join(DEFAULT_OUTPUT_DIR, f"{sanitized_input}_{timestamp}")

            # Render according to chosen format
            if format_var.get() == "Both":
                render_diagram(py_code, output_base, font_size_var=font_size_var, bg_color_var=bg_color_var, layout_var=layout_var)
            else:
                # Render only selected format
                code_with_params = _force_diagram_params(
                    py_code,
                    title=sanitized_input,
                    filename_base=output_base,
                    outformat=format_var.get().lower(),
                    font_size=font_size_var.get(),
                    bgcolor=bg_color_var.get(),
                    layout_dir=layout_var.get()
                )       
                code_with_params = _wrap_with_injected_imports(code_with_params)
                _run_python_script(code_with_params, workdir=os.path.dirname(output_base))

            progress_queue.put(('success', output_base))

        except Exception as e:
            progress_queue.put(('error', str(e)))
        finally:
            progress_queue.put(('done', None))

    def start_generate_thread():
        generate_button.config(state=tk.DISABLED)
        Thread(target=generate_task, daemon=True).start()

    generate_button = ttk.Button(button_frame, text="Generate Diagram", command=start_generate_thread)
    generate_button.pack(side="left", padx=5)

    quit_button = ttk.Button(button_frame, text="Quit", command=root.destroy)
    quit_button.pack(side="right", padx=5)

    process_queue()
    root.mainloop()


if __name__ == "__main__":
    logger.info("Application starting.")
    try:
        ollama.list()
    except Exception:
        logger.error("Ollama service not running. Please start the Ollama application and try again.", exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ollama Error", "Could not connect to Ollama service. Please ensure it is running.", parent=root)
        root.destroy()
        raise SystemExit(1)

    # Quick dependency hint
    try:
        import diagrams  # noqa: F401
    except Exception:
        logger.error("The 'diagrams' package is not installed. Please install it with 'pip install diagrams'.", exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Dependency Error", "The 'diagrams' package is not installed. Please install it with 'pip install diagrams'.", parent=root)
        root.destroy()
        raise SystemExit(1)

    gui_main()
    logger.info("Application has been closed.")
