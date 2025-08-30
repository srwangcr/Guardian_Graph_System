from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
import time

# Importar datos desde los módulos core
from core.behavior_monitor import tagged_users
from core.deception_engine import user_count

# Inicializar consola
console = Console()

# Construir layout principal
def build_layout():
    layout = Layout(name="root")

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3)
    )

    layout["body"].split_row(
        Layout(name="users"),
        Layout(name="risk"),
        Layout(name="events")
    )

    layout["header"].update(Text("🛡️ CLI de Defensa Activa", style="bold green"))
    layout["footer"].update(Text("Actualizando cada 2 segundos | Ctrl+C para salir", style="dim"))

    return layout

# Construir tabla de usuarios etiquetados
def build_user_table():
    table = Table(title="Usuarios Etiquetados", box=box.SIMPLE)
    table.add_column("Usuario", style="cyan", no_wrap=True)
    table.add_column("Tags", style="magenta")

    for user, tags in tagged_users.items():
        table.add_row(user, ", ".join(tags))

    return table

# Construir tabla de niveles de riesgo
def build_risk_table():
    table = Table(title="Niveles de Riesgo", box=box.SIMPLE)
    table.add_column("Usuario", style="yellow", no_wrap=True)
    table.add_column("Nivel", style="red")

    risk_data, _ = user_count()
    for user, level in risk_data.items():
        table.add_row(user, level)

    return table

# Panel de eventos recientes (placeholder)
def build_event_panel():
    return Panel(Text("Eventos registrados en system_events.log", style="dim"), title="Eventos")

# Actualizar layout en vivo
def update_layout(layout):
    layout["users"].update(build_user_table())
    layout["risk"].update(build_risk_table())
    layout["events"].update(build_event_panel())

# Función principal del dashboard
def run_dashboard():
    layout = build_layout()
    with Live(layout, refresh_per_second=1, screen=True):
        while True:
            update_layout(layout)
            time.sleep(2)
