import { useEffect, useState } from "react";
import * as adminApi from "../../api/admin";
import { useToast } from "../../context/ToastContext";
import { timeAgo } from "../../utils/format";

export default function AdminUsersPage() {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, limit: 20 });

  const load = async (p = page, query = q) => {
    const res = await adminApi.users({ page: p, limit: 20, q: query || undefined });
    setData(res);
  };

  useEffect(() => {
    load(1, q);
    setPage(1);
  }, [q]);

  useEffect(() => {
    load(page, q);
  }, [page]);

  const remove = async (u) => {
    if (!confirm(`${u.username} 회원을 탈퇴(삭제) 처리할까요?`)) return;
    try {
      await adminApi.deleteUser(u.id);
      toast.success("회원을 삭제했습니다");
      load(page, q);
    } catch (ex) {
      toast.error(ex.response?.data?.detail || "삭제하지 못했습니다");
    }
  };

  const pages = Math.max(1, Math.ceil(data.total / data.limit));

  return (
    <div className="admin-page">
      <h1>회원 관리</h1>
      <input
        className="admin-search"
        placeholder="이름, 사용자명, 이메일 검색"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="admin-meta muted">
        총 {data.total}명 · {page}/{pages} 페이지
      </div>
      <table className="admin-table">
        <thead>
          <tr>
            <th>사용자</th>
            <th>이메일</th>
            <th>게시물</th>
            <th>가입일</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {data.items.map((u) => (
            <tr key={u.id}>
              <td>
                <strong>{u.username}</strong>
                <div className="muted">{u.full_name}</div>
              </td>
              <td>{u.email}</td>
              <td>{u.posts_count}</td>
              <td title={u.created_at}>
                {timeAgo(u.created_at)}
                <div className="muted" style={{ fontSize: 11 }}>
                  {u.created_at}
                </div>
              </td>
              <td>
                <button type="button" className="btn danger" onClick={() => remove(u)}>
                  탈퇴
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!data.items.length && <div className="empty">회원 없음</div>}
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
