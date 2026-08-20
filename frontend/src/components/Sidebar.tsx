import {
  BarChart3,
  Bot,
  CalendarDays,
  Goal,
  Home,
  Shield,
  Trophy,
} from "lucide-react";

import {
  NavLink,
} from "react-router-dom";

import UpdateStatusIndicator from "./UpdateStatusIndicator";


interface NavigationItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}


const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    path: "/",
    label: "Visão Geral",
    icon: <Home size={18} />,
  },
  {
    path: "/classificacao",
    label: "Classificação",
    icon: <Trophy size={18} />,
  },
  {
    path: "/clubes",
    label: "Clubes",
    icon: <Shield size={18} />,
  },
  {
    path: "/evolucao",
    label: "Evolução",
    icon: <BarChart3 size={18} />,
  },
  {
    path: "/jogos",
    label: "Jogos",
    icon: <CalendarDays size={18} />,
  },
  {
    path: "/previsoes",
    label: "Previsões",
    icon: <Bot size={18} />,
  },
];


function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <Goal size={24} />
        </div>

        <div>
          <strong>
            Brasileirão
          </strong>

          <span>
            Data Lab
          </span>
        </div>
      </div>


      <nav className="nav">
        {
          NAVIGATION_ITEMS.map(
            (
              item,
            ) => (
              <NavLink
                key={
                  item.path
                }
                to={
                  item.path
                }
                end={
                  item.path
                  === "/"
                }
                className={
                  ({
                    isActive,
                  }) =>
                    isActive
                      ? "nav-item active"
                      : "nav-item"
                }
              >
                {
                  item.icon
                }

                {
                  item.label
                }
              </NavLink>
            ),
          )
        }
      </nav>


      <UpdateStatusIndicator />
    </aside>
  );
}


export default Sidebar;