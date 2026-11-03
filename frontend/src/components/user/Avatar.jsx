import { mediaUrl } from "../../utils/format";

export default function Avatar({ user, size = "sm", ring, seen }) {
  const cls = size === "xl" ? "avatar xl" : size === "lg" ? "avatar lg" : "avatar";
  const img = user?.avatar_url ? (
    <img className={cls} src={mediaUrl(user.avatar_url)} alt={user.username} />
  ) : (
    <span className={`${cls} avatar-fallback`}>{(user?.username || "?")[0].toUpperCase()}</span>
  );
  if (!ring) return img;
  return (
    <span className={`ring ${seen ? "seen" : ""}`}>
      <span className="ring-inner">{img}</span>
    </span>
  );
}
