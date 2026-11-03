import { useState } from "react";
import * as usersApi from "../../api/users";
import { useToast } from "../../context/ToastContext";
import useRequireLogin from "../../hooks/useRequireLogin";

export default function FollowButton({ user, onChange }) {
  const [following, setFollowing] = useState(user.is_following);
  const toast = useToast();
  const requireLogin = useRequireLogin();
  if (user.is_me) return null;

  const toggle = async () => {
    if (!requireLogin()) return;
    const prev = following;
    setFollowing(!prev);
    try {
      if (prev) await usersApi.unfollow(user.username);
      else await usersApi.follow(user.username);
      onChange?.(!prev);
    } catch {
      setFollowing(prev);
      toast.error("팔로우를 변경하지 못했습니다");
    }
  };

  return (
    <button className="btn" style={{ width: "auto", padding: "6px 16px", background: following ? "#efefef" : undefined, color: following ? "#262626" : "#fff" }} onClick={toggle}>
      {following ? "팔로잉" : "팔로우"}
    </button>
  );
}
