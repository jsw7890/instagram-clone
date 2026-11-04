import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import * as authApi from "../../api/auth";
import { useAuth } from "../../context/AuthContext";
import { formatApiDetail } from "../../utils/apiError";

export default function AdminLoginPage() {
  const { user, login, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  if (user?.is_admin) return <Navigate to="/admin" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await login(username, password);
      const me = await authApi.me();
      if (!me.is_admin) {
        logout();
        setErr("관리자 계정이 아닙니다");
        return;
      }
      nav(loc.state?.from || "/admin", { replace: true });
    } catch (ex) {
      setErr(formatApiDetail(ex.response?.data?.detail, "로그인에 실패했습니다"));
    }
  };

  return (
    <div className="admin-login">
      <form className="auth-card" onSubmit={submit}>
        <h1>관리자 로그인</h1>
        <p className="muted">관리자 전용 영역입니다.</p>
        <input placeholder="관리자 아이디" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        <input
          type="password"
          placeholder="비밀번호"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
        {err && <div className="err">{err}</div>}
        <button className="btn" disabled={!username || !password}>
          로그인
        </button>
        <Link className="link" to="/login" style={{ display: "inline-block", marginTop: 12 }}>
          일반 로그인으로
        </Link>
      </form>
    </div>
  );
}
