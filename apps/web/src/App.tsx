import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth";
import { Layout } from "./components/Layout";
import { ApprovalsPage } from "./pages/Approvals";
import { AuditPage } from "./pages/Audit";
import { DashboardPage } from "./pages/Dashboard";
import { InvestigationDetailPage } from "./pages/InvestigationDetail";
import { LoginPage } from "./pages/Login";
import { NewInvestigationPage } from "./pages/NewInvestigation";

function RequireAuth() {
  const { me, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return <p className="muted">Loading session…</p>;
  }
  if (!me) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

function RequirePermission({ permission }: { permission: string }) {
  const { can } = useAuth();
  if (!can(permission)) {
    return <p className="error">Your role cannot open this page.</p>;
  }
  return <Outlet />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route element={<RequirePermission permission="investigations:create" />}>
            <Route path="/investigations/new" element={<NewInvestigationPage />} />
          </Route>
          <Route path="/investigations/:id" element={<InvestigationDetailPage />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
