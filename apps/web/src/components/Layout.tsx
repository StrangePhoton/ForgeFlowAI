import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export function Layout() {
  const { me, logout, can } = useAuth();
  return (
    <>
      <header className="app-header">
        <div className="brand">ForgeFlow AI</div>
        <nav className="nav">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          {can("investigations:create") ? <NavLink to="/investigations/new">New investigation</NavLink> : null}
          <NavLink to="/approvals">Approvals</NavLink>
          <NavLink to="/audit">Audit log</NavLink>
        </nav>
        <div className="who">
          <span>
            {me?.username} · {me?.role}
          </span>
          <button className="secondary" type="button" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}
