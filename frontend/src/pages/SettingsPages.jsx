import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as authApi from "../api/auth";
import * as usersApi from "../api/users";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export function SettingsHome() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="settings-page">
      <h2>설정</h2>
      <Link className="settings-row" to="/settings/password">
        <span>비밀번호 변경</span>
        <span className="muted">›</span>
      </Link>
      <Link className="settings-row" to="/settings/privacy">
        <span>개인정보 및 보안</span>
        <span className="muted">›</span>
      </Link>
      <button
        type="button"
        className="settings-row settings-logout"
        onClick={() => {
          logout();
          navigate("/login");
        }}
      >
        <span>로그아웃</span>
      </button>
    </div>
  );
}

export function PasswordSettings() {
  const toast = useToast();
  const [currentPassword, setCurrent] = useState("");
  const [newPassword, setNew] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirm) {
      toast.error("새 비밀번호가 일치하지 않습니다");
      return;
    }
    setBusy(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast.success("비밀번호를 변경했습니다");
      setCurrent("");
      setNew("");
      setConfirm("");
    } catch (ex) {
      toast.error(ex.response?.data?.detail || "비밀번호를 변경하지 못했습니다");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="settings-page">
      <Link className="muted" to="/settings">
        ← 설정
      </Link>
      <h2>비밀번호 변경</h2>
      <form onSubmit={submit} className="settings-form">
        <input type="password" placeholder="현재 비밀번호" value={currentPassword} onChange={(e) => setCurrent(e.target.value)} />
        <input type="password" placeholder="새 비밀번호 (8자 이상)" value={newPassword} onChange={(e) => setNew(e.target.value)} />
        <input type="password" placeholder="새 비밀번호 확인" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        <button className="btn" disabled={busy || !currentPassword || newPassword.length < 8}>
          변경하기
        </button>
      </form>
    </div>
  );
}

export function PrivacySettings() {
  const toast = useToast();
  const [privacy, setPrivacy] = useState(null);

  useEffect(() => {
    usersApi.getPrivacy().then(setPrivacy).catch(() => {});
  }, []);

  const toggle = async (key) => {
    const next = { ...privacy, [key]: !privacy[key] };
    setPrivacy(next);
    try {
      const saved = await usersApi.updatePrivacy({ [key]: next[key] });
      setPrivacy(saved);
      toast.success("저장했습니다");
    } catch {
      setPrivacy(privacy);
      toast.error("설정을 저장하지 못했습니다");
    }
  };

  if (!privacy) return <div className="spinner" />;

  return (
    <div className="settings-page">
      <Link className="muted" to="/settings">
        ← 설정
      </Link>
      <h2>개인정보 및 보안</h2>
      <label className="settings-row">
        <div>
          <div>비공개 계정</div>
          <div className="muted">팔로워만 게시물을 볼 수 있습니다.</div>
        </div>
        <input type="checkbox" checked={privacy.is_private} onChange={() => toggle("is_private")} />
      </label>
      <label className="settings-row">
        <div>
          <div>활동 상태 표시</div>
          <div className="muted">다른 사람에게 최근 활동 여부를 보여줍니다.</div>
        </div>
        <input type="checkbox" checked={privacy.show_activity_status} onChange={() => toggle("show_activity_status")} />
      </label>
    </div>
  );
}
