import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import useRequireLogin from "../../hooks/useRequireLogin";
import { Compass, Gear, Heart, Home, Messenger, Plus, Search } from "../Icons";
import Avatar from "../user/Avatar";

export default function Sidebar({ onCreate, unread }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const requireLogin = useRequireLogin();

  const item = (to, icon, label, extra) => (
    <NavLink to={to} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
      {icon}
      <span>{label}</span>
      {extra}
    </NavLink>
  );

  const gated = (to, icon, label, extra) => {
    if (user) return item(to, icon, label, extra);
    return (
      <button className="nav-item" onClick={requireLogin}>
        {icon}
        <span>{label}</span>
        {extra}
      </button>
    );
  };

  return (
    <aside className="sidebar">
      <Link to="/" className="logo">
        Instagram
      </Link>
      {item("/", <Home />, "홈")}
      {item("/search", <Search />, "검색")}
      {item("/explore", <Compass />, "탐색")}
      {gated("/direct", <Messenger />, "메시지")}
      {gated("/activity", <Heart />, "알림", unread ? <span className="badge" /> : null)}
      <button className="nav-item" onClick={onCreate}>
        <Plus />
        <span>만들기</span>
      </button>
      {user ? (
        item(`/${user.username}`, <Avatar user={user} />, "프로필")
      ) : (
        <button className="nav-item" onClick={requireLogin}>
          <Avatar user={{ username: "게스트" }} />
          <span>프로필</span>
        </button>
      )}
      <div style={{ flex: 1 }} />
      {gated("/settings", <Gear />, "설정")}
      {user ? (
        <button
          className="nav-item"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          로그아웃
        </button>
      ) : (
        <Link className="nav-item" to="/login">
          로그인
        </Link>
      )}
    </aside>
  );
}
