import { Link } from "react-router-dom";
import { compactNumber, mediaUrl } from "../../utils/format";

export default function PostGrid({ items }) {
  if (!items?.length) return <div className="empty">게시물 없음</div>;
  return (
    <div className="grid">
      {items.map((p) => (
        <Link key={p.id} to={`/p/${p.id}`} className="grid-item">
          {p.cover_url && <img src={mediaUrl(p.cover_url)} alt="" />}
          <div className="grid-hover">
            <span>♥ {compactNumber(p.likes_count)}</span>
            <span>💬 {compactNumber(p.comments_count)}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
