import {
  Component,
} from "react";

import type {
  ErrorInfo,
  ReactNode,
} from "react";

import {
  Home,
  RefreshCcw,
  TriangleAlert,
} from "lucide-react";


interface RouteErrorBoundaryProps {
  children: ReactNode;
}


interface RouteErrorBoundaryState {
  hasError: boolean;
}


class RouteErrorBoundary extends Component<
  RouteErrorBoundaryProps,
  RouteErrorBoundaryState
> {
  state: RouteErrorBoundaryState = {
    hasError: false,
  };


  static getDerivedStateFromError():
    RouteErrorBoundaryState {
    return {
      hasError: true,
    };
  }


  componentDidCatch(
    error: Error,
    info: ErrorInfo,
  ) {
    console.error(
      "Erro inesperado ao renderizar a rota:",
      error,
      info,
    );
  }


  private reloadPage = () => {
    window.location.reload();
  };


  private goHome = () => {
    window.location.href = "/";
  };


  render() {
    if (
      !this.state.hasError
    ) {
      return this.props.children;
    }


    return (
      <section
        className="panel"
        style={{
          maxWidth: "620px",
          margin: "0 auto",
        }}
      >
        <div className="panel-header">
          <div className="panel-icon">
            <TriangleAlert
              size={19}
            />
          </div>

          <div>
            <h2>
              Não foi possível abrir esta página
            </h2>

            <p>
              Ocorreu um erro inesperado
              ao carregar este conteúdo.
            </p>
          </div>
        </div>


        <div
          style={{
            padding: "20px",
            display: "flex",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <button
            type="button"
            onClick={
              this.reloadPage
            }
            style={{
              minHeight: "40px",
              padding:
                "0 14px",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              border:
                "1px solid #28513e",
              borderRadius: "9px",
              background:
                "rgba(39, 214, 134, 0.10)",
              color: "#eafff3",
              cursor: "pointer",
              fontWeight: 700,
            }}
          >
            <RefreshCcw
              size={16}
            />

            Tentar novamente
          </button>


          <button
            type="button"
            onClick={
              this.goHome
            }
            style={{
              minHeight: "40px",
              padding:
                "0 14px",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              border:
                "1px solid #252f35",
              borderRadius: "9px",
              background:
                "#11181d",
              color: "#aab6b0",
              cursor: "pointer",
              fontWeight: 700,
            }}
          >
            <Home
              size={16}
            />

            Voltar ao início
          </button>
        </div>
      </section>
    );
  }
}


export default RouteErrorBoundary;