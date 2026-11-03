import { Link } from "react-router-dom";
import Avatar from "./Avatar";
import FollowButton from "./FollowButton";

export default function SuggestedUsers({ users, onRemove, className = "" }) {
  if (!users?.length) {
    return (
      <div className={`suggested-users ${className}`}>
        <div className="muted" style={{ marginBottom: 12, fontWeight: 600 }}>
          회원님을 위한 추천
        </div>
        <div className="empty" style={{ padding: "16px 0" }}>
          지금은 추천할 새 계정이 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div className={`suggested-users ${className}`}>
      <div className="muted" style={{ marginBottom: 12, fontWeight: 600 }}>
        회원님을 위한 추천
      </div>
      {users.map((u) => (
        <div className="user-row" key={u.id}>
          <Link to={`/${u.username}`}>
            <Avatar user={u} />
          </Link>
          <div className="meta">
            <Link className="name" to={`/${u.username}`}>
              {u.username}
            </Link>
            <div className="sub">{u.full_name}</div>
          </div>
          <FollowButton
            user={u}
            onChange={(nowFollowing) => {
              if (nowFollowing) onRemove?.(u.id);
            }}
          />
        </div>
      ))}
    </div>
  );
}
