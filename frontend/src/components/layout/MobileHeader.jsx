import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Gear, Messenger } from "../Icons";

export default function MobileHeader() {
  const { user } = useAuth();

  return (
    <header className="mobile-header">
      <Link to="/" className="mobile-header-logo">
        Instagram
      </Link>
      {user ? (
        <div className="mobile-header-actions">
          <Link to="/direct" className="icon-btn" aria-label="메시지">
            <Messenger />
          </Link>
          <Link to="/settings" className="icon-btn" aria-label="설정">
            <Gear />
          </Link>
        </div>
      ) : (
        <Link to="/login" className="mobile-header-login">
          로그인
        </Link>
      )}
    </header>
  );
}
