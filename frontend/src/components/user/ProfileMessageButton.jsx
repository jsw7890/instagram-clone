import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as msgApi from "../../api/messages";
import { useToast } from "../../context/ToastContext";
import useRequireLogin from "../../hooks/useRequireLogin";
import { formatApiDetail } from "../../utils/apiError";

export default function ProfileMessageButton({ username }) {
  const requireLogin = useRequireLogin();
  const navigate = useNavigate();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  const open = async () => {
    if (!requireLogin()) return;
    setBusy(true);
    try {
      const conv = await msgApi.openConversation(username);
      navigate(`/direct/${conv.id}`);
    } catch (ex) {
      toast.error(formatApiDetail(ex.response?.data?.detail, "대화를 시작하지 못했습니다"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <button type="button" className="btn profile-msg-btn" disabled={busy} onClick={open}>
      메시지
    </button>
  );
}
