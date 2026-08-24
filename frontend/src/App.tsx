import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Sidebar from "./components/Sidebar";

import ClubComparisonPage from "./pages/ClubComparisonPage";
import ClubDetailsPage from "./pages/ClubDetailsPage";
import ClubsPage from "./pages/ClubsPage";
import EvolutionPage from "./pages/EvolutionPage";
import GamesPage from "./pages/GamesPage";
import OverviewPage from "./pages/OverviewPage";
import PredictionsPage from "./pages/PredictionsPage";
import StandingsPage from "./pages/StandingsPage";

import "./App.css";


function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />

        <main className="content">
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
        </main>
      </div>
    </BrowserRouter>
  );
}


export default App;