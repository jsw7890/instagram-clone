import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function useRequireLogin() {
  const { user } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();

  return () => {
    if (user) return true;
    nav("/login", { state: { from: loc.pathname } });
    return false;
  };
}
