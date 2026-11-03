import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import useRequireLogin from "../../hooks/useRequireLogin";
import { Compass, Heart, Home, Plus } from "../Icons";
import Avatar from "../user/Avatar";

export default function BottomNav({ onCreate }) {
  const { user } = useAuth();
  const requireLogin = useRequireLogin();
  return (
    <nav className="bottom-nav">
      <NavLink to="/" className="icon-btn" aria-label="홈">
        <Home />
      </NavLink>
      <NavLink to="/explore" className="icon-btn" aria-label="탐색">
        <Compass />
      </NavLink>
      <button className="icon-btn" onClick={onCreate} aria-label="만들기">
        <Plus />
      </button>
      {user ? (
        <NavLink to="/activity" className="icon-btn" aria-label="알림">
          <Heart />
        </NavLink>
      ) : (
        <button className="icon-btn" onClick={requireLogin} aria-label="알림">
          <Heart />
        </button>
      )}
      {user ? (
        <NavLink to={`/${user.username}`} className="icon-btn" aria-label="프로필">
          <Avatar user={user} />
        </NavLink>
      ) : (
        <button className="icon-btn" onClick={requireLogin} aria-label="프로필">
          <Avatar user={{ username: "게스트" }} />
        </button>
      )}
    </nav>
  );
}
