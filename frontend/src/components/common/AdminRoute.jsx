import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function AdminRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div className="spinner" />;
  if (!user) return <Navigate to="/admin/login" replace state={{ from: "/admin" }} />;
  if (!user.is_admin) return <Navigate to="/" replace />;
  return <Outlet />;
}
