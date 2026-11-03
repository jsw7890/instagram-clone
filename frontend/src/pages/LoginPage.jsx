import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import SiteFooter from "../components/layout/SiteFooter";
import * as authApi from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { formatApiDetail } from "../utils/apiError";

export default function LoginPage() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await login(username, password);
      const me = await authApi.me();
      nav(me.is_admin ? "/admin" : loc.state?.from || "/", { replace: true });
    } catch (ex) {
      setErr(formatApiDetail(ex.response?.data?.detail, "로그인에 실패했습니다"));
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1 className="logo">Instagram</h1>
        <input placeholder="사용자 이름 또는 이메일" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="비밀번호" value={password} onChange={(e) => setPassword(e.target.value)} />
        {err && <div className="err">{String(err)}</div>}
        <button className="btn" disabled={!username || !password}>
          로그인
        </button>
        <p className="muted" style={{ marginTop: 24 }}>
          데모 계정 demo / demo1234
        </p>
        <p className="muted">
          <Link className="link" to="/admin/login">
            관리자 로그인
          </Link>
        </p>
      </form>
      <div className="auth-card" style={{ padding: 20 }}>
        계정이 없으신가요? <Link className="link" to="/signup">가입하기</Link>
        <div className="muted" style={{ marginTop: 12 }}>
          <Link className="link" to="/">로그인 없이 둘러보기</Link>
        </div>
      </div>
      <SiteFooter />
    </div>
  );
}
