import {
  useEffect,
  useState,
} from "react";

import {
  CheckCircle2,
  Clock3,
  RefreshCw,
} from "lucide-react";

import {
  getUpdateStatus,
  type UpdateStatus,
} from "../api";

import "./UpdateStatusIndicator.css";


function formatUpdateDate(
  value: string,
): string {
  const date = new Date(
    value,
  );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Horário indisponível";
  }

  return new Intl.DateTimeFormat(
    "pt-BR",
    {
      timeZone:
        "America/Sao_Paulo",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    date,
  );
}


function UpdateStatusIndicator() {
  const [
    status,
    setStatus,
  ] = useState<
    UpdateStatus | null
  >(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );

  const [
    failed,
    setFailed,
  ] = useState(
    false,
  );


  useEffect(
    () => {
      let active = true;

      async function loadStatus() {
        try {
          const result =
            await getUpdateStatus();

          if (!active) {
            return;
          }

          setStatus(
            result,
          );

          setFailed(
            false,
          );
        } catch {
          if (!active) {
            return;
          }

          setFailed(
            true,
          );
        } finally {
          if (active) {
            setLoading(
              false,
            );
          }
        }
      }

      loadStatus();

      return () => {
        active = false;
      };
    },
    [],
  );


  if (loading) {
    return (
      <div
        className="update-status"
        aria-live="polite"
      >
        <div className="update-status-icon loading">
          <RefreshCw
            size={16}
          />
        </div>

        <div className="update-status-content">
          <strong>
            Verificando dados
          </strong>

          <span>
            Consultando status...
          </span>
        </div>
      </div>
    );
  }


  if (
    failed
    || !status
  ) {
    return (
      <div
        className="update-status"
        aria-live="polite"
      >
        <div className="update-status-icon unavailable">
          <Clock3
            size={16}
          />
        </div>

        <div className="update-status-content">
          <strong>
            Status indisponível
          </strong>

          <span>
            Dados continuam acessíveis
          </span>
        </div>
      </div>
    );
  }


  return (
    <div
      className="update-status"
      aria-live="polite"
    >
      <div className="update-status-icon success">
        <CheckCircle2
          size={16}
        />
      </div>

      <div className="update-status-content">
        <div className="update-status-title">
          <strong>
            Dados atualizados
          </strong>

          <span className="update-status-live-dot" />
        </div>

        <span>
          {
            formatUpdateDate(
              status.last_sync_at_utc,
            )
          }
        </span>

        <small>
          Fonte {status.source}
          {" • "}
          {
            status.automation_enabled
              ? "Automático"
              : "Manual"
          }
        </small>

        <small>
          {status.played_matches} jogados
          {" • "}
          {status.future_matches} futuros
        </small>
      </div>
    </div>
  );
}


export default UpdateStatusIndicator;