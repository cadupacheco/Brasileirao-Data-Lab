from __future__ import annotations

from brasileirao_data_lab.pipelines.update_detector import (
    CURRENT_SEASON,
    check_for_updates,
    print_update_check,
)


def main() -> None:
    print()
    print("⚽ Brasileirão Data Lab - Update Detector V0.7")
    print(
        f"[INFO] Verificando alterações na temporada "
        f"{CURRENT_SEASON}."
    )
    print(
        "[INFO] Esta etapa apenas compara os dados. "
        "Nenhum arquivo será sobrescrito."
    )

    result = check_for_updates()

    print_update_check(
        result
    )


if __name__ == "__main__":
    main()