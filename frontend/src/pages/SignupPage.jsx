import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import SiteFooter from "../components/layout/SiteFooter";
import { useAuth } from "../context/AuthContext";
import { formatApiDetail } from "../utils/apiError";
import { normalizeSignupPayload, validateSignupPayload } from "../utils/signupValidation";

export default function SignupPage() {
  const { user, signup } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ email: "", full_name: "", username: "", password: "" });
  const [err, setErr] = useState("");
  if (user) return <Navigate to="/" replace />;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    const payload = normalizeSignupPayload(form);
    const validationErr = validateSignupPayload(payload);
    if (validationErr) {
      setErr(validationErr);
      return;
    }
    try {
      await signup(payload);
      nav("/", { replace: true });
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(formatApiDetail(d, "가입에 실패했습니다"));
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1 className="logo">Instagram</h1>
        <p className="muted">친구들의 사진과 동영상을 보려면 가입하세요.</p>
        <input placeholder="이메일" value={form.email} onChange={set("email")} />
        <input placeholder="성명" value={form.full_name} onChange={set("full_name")} />
        <input
          placeholder="사용자 이름 (영문·숫자·_·.)"
          value={form.username}
          onChange={set("username")}
          autoComplete="username"
        />
        <input type="password" placeholder="비밀번호 (8자 이상)" value={form.password} onChange={set("password")} />
        <p className="muted" style={{ fontSize: 12, margin: "4px 0 0" }}>
          사용자 이름에 한글·공백·하이픈(-)은 사용할 수 없습니다.
        </p>
        {err && <div className="err">{err}</div>}
        <button className="btn" disabled={!form.email || !form.username || form.password.length < 8}>
          가입
        </button>
      </form>
      <div className="auth-card" style={{ padding: 20 }}>
        계정이 있으신가요? <Link className="link" to="/login">로그인</Link>
        <div className="muted" style={{ marginTop: 12 }}>
          <Link className="link" to="/">가입 없이 둘러보기</Link>
        </div>
      </div>
      <SiteFooter />
    </div>
  );
}
