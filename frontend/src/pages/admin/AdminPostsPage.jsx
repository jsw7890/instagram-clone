import { useEffect, useState } from "react";
import * as adminApi from "../../api/admin";
import { useToast } from "../../context/ToastContext";
import { mediaUrl, timeAgo } from "../../utils/format";

export default function AdminPostsPage() {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, limit: 20 });

  const load = async (p = page, query = q) => {
    const res = await adminApi.posts({ page: p, limit: 20, q: query || undefined });
    setData(res);
  };

  useEffect(() => {
    load(1, q);
    setPage(1);
  }, [q]);

  useEffect(() => {
    load(page, q);
  }, [page]);

  const remove = async (post) => {
    if (!confirm(`게시물 #${post.id}을(를) 삭제할까요?`)) return;
    try {
      await adminApi.deletePost(post.id);
      toast.success("게시물을 삭제했습니다");
      load(page, q);
    } catch (ex) {
      toast.error(ex.response?.data?.detail || "삭제하지 못했습니다");
    }
  };

  const pages = Math.max(1, Math.ceil(data.total / data.limit));

  return (
    <div className="admin-page">
      <h1>게시물 관리</h1>
      <input
        className="admin-search"
        placeholder="캡션·위치 검색"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="admin-meta muted">
        총 {data.total}건 · {page}/{pages} 페이지
      </div>
      <div className="admin-post-list">
        {data.items.map((p) => (
          <article key={p.id} className="admin-post-row">
            {p.cover_url ? (
              <img src={mediaUrl(p.cover_url)} alt="" className="admin-post-thumb" />
            ) : (
              <div className="admin-post-thumb empty">없음</div>
            )}
            <div className="admin-post-body">
              <div>
                <strong>#{p.id}</strong> · @{p.author.username}
              </div>
              <div className="muted">{p.caption || "(캡션 없음)"}</div>
              <div className="muted" style={{ fontSize: 12 }}>
                ♥ {p.likes_count} · 💬 {p.comments_count} · {p.image_count}장 · {timeAgo(p.created_at)}
              </div>
            </div>
            <button type="button" className="btn danger" onClick={() => remove(p)}>
              삭제
            </button>
          </article>
        ))}
      </div>
      {!data.items.length && <div className="empty">게시물 없음</div>}
      <div className="admin-pager">
        <button type="button" className="btn ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          이전
        </button>
        <button type="button" className="btn ghost" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
          다음
        </button>
      </div>
    </div>
  );
}
