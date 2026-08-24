import {
  lazy,
  Suspense,
} from "react";

import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import {
  LoaderCircle,
} from "lucide-react";

import RouteErrorBoundary from "./components/RouteErrorBoundary";
import Sidebar from "./components/Sidebar";

import "./App.css";


const OverviewPage = lazy(
  () =>
    import(
      "./pages/OverviewPage"
    ),
);

const StandingsPage = lazy(
  () =>
    import(
      "./pages/StandingsPage"
    ),
);

const ClubsPage = lazy(
  () =>
    import(
      "./pages/ClubsPage"
    ),
);

const ClubDetailsPage = lazy(
  () =>
    import(
      "./pages/ClubDetailsPage"
    ),
);

const ClubComparisonPage = lazy(
  () =>
    import(
      "./pages/ClubComparisonPage"
    ),
);

const EvolutionPage = lazy(
  () =>
    import(
      "./pages/EvolutionPage"
    ),
);

const GamesPage = lazy(
  () =>
    import(
      "./pages/GamesPage"
    ),
);

const PredictionsPage = lazy(
  () =>
    import(
      "./pages/PredictionsPage"
    ),
);


function PageLoading() {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-icon">
          <LoaderCircle
            size={19}
          />
        </div>

        <div>
          <h2>
            Carregando página...
          </h2>

          <p>
            Preparando os dados
            e componentes necessários.
          </p>
        </div>
      </div>
    </div>
  );
}


function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />

        <main className="content">
          <RouteErrorBoundary>
            <Suspense
              fallback={
                <PageLoading />
              }
            >
              <Routes>
                <Route
                  path="/"
                  element={
                    <OverviewPage />
                  }
                />

                <Route
                  path="/classificacao"
                  element={
                    <StandingsPage />
                  }
                />

                <Route
                  path="/clubes"
                  element={
                    <ClubsPage />
                  }
                />

                <Route
                  path="/clubes/:teamId"
                  element={
                    <ClubDetailsPage />
                  }
                />

                <Route
                  path="/comparacao"
                  element={
                    <ClubComparisonPage />
                  }
                />

                <Route
                  path="/evolucao"
                  element={
                    <EvolutionPage />
                  }
                />

                <Route
                  path="/jogos"
                  element={
                    <GamesPage />
                  }
                />

                <Route
                  path="/previsoes"
                  element={
                    <PredictionsPage />
                  }
                />

                <Route
                  path="*"
                  element={
                    <Navigate
                      to="/"
                      replace
                    />
                  }
                />
              </Routes>
            </Suspense>
          </RouteErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  );
}


export default App;