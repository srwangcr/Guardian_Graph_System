from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Guardian Graph System")
    parser.add_argument("--config", default="config.yaml", help="Ruta del archivo YAML de configuración")
    parser.add_argument("--demo", action="store_true", help="Ejecutar el modo demo en lugar del dashboard")
    parser.add_argument("--api", action="store_true", help="Ejecutar API REST protegida por OAuth2 bearer")
    parser.add_argument("--api-host", default="0.0.0.0", help="Host para API REST")
    parser.add_argument("--api-port", type=int, default=8080, help="Puerto para API REST")
    parser.add_argument("--containment-agent", action="store_true", help="Ejecutar agente privilegiado de contencion")
    parser.add_argument("--iterations", type=int, default=8, help="Cantidad de ciclos para el modo demo")
    parser.add_argument("--metrics-port", type=int, default=8000, help="Puerto Prometheus para el modo demo")
    args = parser.parse_args()

    os.environ["GGS_CONFIG_PATH"] = args.config

    if args.demo:
        from core.demo_runner import run_demo

        run_demo(iterations=args.iterations, metrics_port=args.metrics_port)
        return

    if args.api:
        from utils.api_server import run_api_server

        run_api_server(host=args.api_host, port=args.api_port)
        return

    if args.containment_agent:
        from core.containment_system import run_containment_agent

        run_containment_agent()
        return

    from utils.cli_dashboard import run_dashboard

    run_dashboard()


if __name__ == "__main__":
    main()
