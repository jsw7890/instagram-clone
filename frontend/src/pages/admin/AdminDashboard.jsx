import { useEffect, useState } from "react";
import * as adminApi from "../../api/admin";
import { timeAgo } from "../../utils/format";

function StatCard({ label, value }) {
  return (
    <div className="admin-stat">
      <div className="admin-stat-value">{value?.toLocaleString?.() ?? value}</div>
      <div className="admin-stat-label">{label}</div>
    </div>
  );
}

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    adminApi
      .stats()
      .then(setData)
      .catch(() => setErr("통계를 불러오지 못했습니다"));
  }, []);

  if (err) return <div className="admin-page empty">{err}</div>;
  if (!data) return <div className="spinner" />;

  return (
    <div className="admin-page">
      <h1>통계 대시보드</h1>
      <p className="muted">서비스 전체 현황입니다.</p>
      <div className="admin-stat-grid">
        <StatCard label="회원" value={data.users} />
        <StatCard label="게시물" value={data.posts} />
        <StatCard label="댓글" value={data.comments} />
        <StatCard label="좋아요" value={data.likes} />
        <StatCard label="팔로우" value={data.follows} />
        <StatCard label="메시지" value={data.messages} />
        <StatCard label="스토리" value={data.stories} />
        <StatCard label="7일 신규 가입" value={data.signups_last_7_days} />
        <StatCard label="7일 신규 게시" value={data.posts_last_7_days} />
      </div>
      <section className="admin-panel">
        <h2>최근 가입</h2>
        {!data.recent_signups?.length && <div className="muted">최근 7일 가입 없음</div>}
        <table className="admin-table">
          <thead>
            <tr>
              <th>사용자</th>
              <th>이메일</th>
              <th>가입일</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_signups?.map((u) => (
              <tr key={u.id}>
                <td>
                  <strong>{u.username}</strong>
                  <div className="muted">{u.full_name}</div>
                </td>
                <td>{u.email}</td>
                <td>{timeAgo(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
