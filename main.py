import rich.console
import rich.table
import rich.panel
import rich.live 
import rich.layout
import rich.text 
import threading
import time

# Importar módulos del sistema
import core.behavior_monitor 
import core.deception_engine 
import core.honeypot_files 
import core.containment_system 

import utils.config_manager 
import utils.event_logger 



from utils.cli_dashboard import run_dashboard

if __name__ == "__main__":
    run_dashboard()
