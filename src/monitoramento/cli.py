import argparse

from .mission import MissionController
from .models import Coordinate, MissionConfig, Telemetry
from .routes import polygon_survey


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador do computador de missão")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if not args.demo:
        parser.error("a primeira versão oferece apenas --demo")
    base = Coordinate(-23.5505, -46.6333, 100)
    area = [Coordinate(-23.5505, -46.6333, 100), Coordinate(-23.5505, -46.6313, 100), Coordinate(-23.5485, -46.6313, 100), Coordinate(-23.5485, -46.6333, 100)]
    controller = MissionController(polygon_survey(base, area, spacing_m=100), MissionConfig(return_battery_percent=30))
    controller.start()
    target = controller.update(Telemetry(base, 80))
    print(f"fonte={controller.plan.source} pontos={len(controller.plan.route)} proximo_alvo={target}")
    target = controller.update(Telemetry(base, 29))
    print(f"bateria=29% estado={controller.state.value} retorno={target}")


if __name__ == "__main__":
    main()
