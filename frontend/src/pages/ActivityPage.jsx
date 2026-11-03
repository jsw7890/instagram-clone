import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as notifApi from "../api/notifications";
import Avatar from "../components/user/Avatar";
import { useToast } from "../context/ToastContext";
import { timeAgo } from "../utils/format";

const text = (n) => {
  if (n.type === "follow") return "님이 회원님을 팔로우하기 시작했습니다.";
  if (n.type === "like") return "님이 회원님의 게시물을 좋아합니다.";
  if (n.type === "comment") return `님이 댓글을 남겼습니다: ${n.comment_preview || ""}`;
  if (n.type === "mention") return "님이 회원님을 언급했습니다.";
  return n.type;
};

export default function ActivityPage() {
  const toast = useToast();
  const [items, setItems] = useState([]);
  useEffect(() => {
    notifApi.listNotifications().then(async (d) => {
      setItems(d.items);
      await notifApi.readNotifications();
    });
  }, []);

  const removeOne = async (e, id) => {
    e.preventDefault();
    e.stopPropagation();
    const prev = items;
    setItems((xs) => xs.filter((x) => x.id !== id));
    try {
      await notifApi.deleteNotification(id);
      toast.success("알림을 삭제했습니다");
    } catch {
      setItems(prev);
      toast.error("알림을 삭제하지 못했습니다. 백엔드를 다시 실행해 주세요.");
    }
  };

  return (
    <div className="activity">
      <h2>알림</h2>
      {items.map((n) => (
        <div key={n.id} className="user-row" style={{ padding: "10px 0", opacity: n.read ? 0.7 : 1 }}>
          <Link to={n.post_id ? `/p/${n.post_id}` : `/${n.actor.username}`} className="user-row" style={{ flex: 1, margin: 0 }}>
            <Avatar user={n.actor} />
            <div>
              <strong>{n.actor.username}</strong>
              {text(n)}
              <div className="muted">{timeAgo(n.created_at)}</div>
            </div>
          </Link>
          <button type="button" className="btn danger" onClick={(e) => removeOne(e, n.id)}>
            삭제
          </button>
        </div>
      ))}
      {!items.length && <div className="empty">알림이 없습니다.</div>}
    </div>
  );
}
