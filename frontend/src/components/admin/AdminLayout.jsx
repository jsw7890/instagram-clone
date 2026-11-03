import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const link = (to, label) => (
    <NavLink to={to} end={to === "/admin"} className={({ isActive }) => (isActive ? "on" : "")}>
      {label}
    </NavLink>
  );

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">Instagram Admin</div>
        <nav>
          {link("/admin", "대시보드")}
          {link("/admin/users", "회원 관리")}
          {link("/admin/posts", "게시물 관리")}
        </nav>
        <div className="admin-sidebar-foot">
          <div className="muted">{user?.username}</div>
          <button
            type="button"
            className="btn ghost"
            onClick={() => {
              logout();
              navigate("/admin/login");
            }}
          >
            로그아웃
          </button>
          <a className="link" href="/">
            앱으로
          </a>
        </div>
      </aside>
      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}
