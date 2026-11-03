import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import * as usersApi from "../api/users";
import PostGrid from "../components/post/PostGrid";
import Avatar from "../components/user/Avatar";

export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const q0 = params.get("q") || "";
  const [q, setQ] = useState(q0);
  const [tab, setTab] = useState("users");
  const [data, setData] = useState({ users: [], hashtags: [], posts: [] });

  useEffect(() => {
    if (q.trim().length < 1) return;
    const t = setTimeout(() => {
      setParams({ q });
      usersApi.searchAll(q).then(setData);
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <div className="search-page">
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="검색" />
      <div className="tabs">
        <button className={tab === "users" ? "on" : ""} onClick={() => setTab("users")}>
          계정
        </button>
        <button className={tab === "hashtags" ? "on" : ""} onClick={() => setTab("hashtags")}>
          태그
        </button>
        <button className={tab === "posts" ? "on" : ""} onClick={() => setTab("posts")}>
          게시물
        </button>
      </div>
      {tab === "users" &&
        data.users.map((u) => (
          <Link key={u.id} to={`/${u.username}`} className="user-row" style={{ padding: "8px 0" }}>
            <Avatar user={u} />
            <div>
              <div className="name">{u.username}</div>
              <div className="sub">{u.full_name}</div>
            </div>
          </Link>
        ))}
      {tab === "hashtags" &&
        data.hashtags.map((h) => (
          <button key={h.name} className="user-row" style={{ width: "100%", background: "none", border: 0 }} onClick={() => { setQ(h.name); setTab("posts"); }}>
            <div>
              <div className="name">#{h.name}</div>
              <div className="sub">{h.posts_count} 게시물</div>
            </div>
          </button>
        ))}
      {tab === "posts" && <PostGrid items={data.posts} />}
    </div>
  );
}
