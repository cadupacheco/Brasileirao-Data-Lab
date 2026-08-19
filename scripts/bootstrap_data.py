from __future__ import annotations

import time

import requests

from brasileirao_data_lab.pipelines.update_data import (
    update_data,
)


MAX_ATTEMPTS = 4
INITIAL_DELAY_SECONDS = 10


def main() -> None:
    """
    Prepara os dados necessários para o deploy.

    Erros de rede vindos da CBF são
    tentados novamente automaticamente.
    Outros erros continuam falhando
    imediatamente para não esconder
    problemas reais do código.
    """

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):
        try:
            print(
                "[INFO] Preparando dados "
                f"para deploy "
                f"(tentativa {attempt}/"
                f"{MAX_ATTEMPTS})..."
            )

            update_data()

            print(
                "[SUCCESS] Dados preparados "
                "para o deploy."
            )

            return

        except requests.RequestException as error:
            if attempt >= MAX_ATTEMPTS:
                print(
                    "[ERROR] Não foi possível "
                    "coletar os dados após "
                    f"{MAX_ATTEMPTS} tentativas."
                )

                raise

            delay = (
                INITIAL_DELAY_SECONDS
                * attempt
            )

            print(
                "[WARN] Falha temporária "
                "na comunicação com a CBF."
            )

            print(
                f"[WARN] {error}"
            )

            print(
                "[INFO] Nova tentativa em "
                f"{delay} segundos..."
            )

            time.sleep(
                delay
            )


if __name__ == "__main__":
    main()