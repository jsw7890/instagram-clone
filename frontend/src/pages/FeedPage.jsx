import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import * as postsApi from "../api/posts";
import * as usersApi from "../api/users";
import PostCard from "../components/post/PostCard";
import StoryBar from "../components/story/StoryBar";
import Avatar from "../components/user/Avatar";
import SuggestedUsers from "../components/user/SuggestedUsers";
import { useAuth } from "../context/AuthContext";

export default function FeedPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [cursor, setCursor] = useState(undefined);
  const [suggested, setSuggested] = useState([]);
  const [loading, setLoading] = useState(true);
  const sentinel = useRef();

  const loadSuggested = useCallback(() => {
    usersApi
      .suggested()
      .then((data) => setSuggested(Array.isArray(data) ? data : []))
      .catch(() => setSuggested([]));
  }, []);

  const load = async (c) => {
    const data = await postsApi.feed(c || undefined);
    setItems((prev) => (c ? [...prev, ...data.items] : data.items));
    setCursor(data.next_cursor);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    loadSuggested();
  }, [user?.id, loadSuggested]);

  useEffect(() => {
    if (!sentinel.current) return;
    const io = new IntersectionObserver((ents) => {
      if (ents[0].isIntersecting && cursor) load(cursor);
    });
    io.observe(sentinel.current);
    return () => io.disconnect();
  }, [cursor]);

  const removeSuggested = (id) => setSuggested((xs) => xs.filter((x) => x.id !== id));

  return (
    <div className="feed-layout">
      <div className="feed-col">
        {user && <StoryBar />}
        <SuggestedUsers users={suggested} onRemove={removeSuggested} className="suggested-inline" />
        {items.map((p) => (
          <PostCard key={p.id} post={p} onDeleted={(id) => setItems((xs) => xs.filter((x) => x.id !== id))} />
        ))}
        {loading && <div className="spinner" />}
        {!loading && !items.length && (
          <div className="empty">{user ? "팔로우한 사람의 게시물이 없습니다." : "아직 게시물이 없습니다."}</div>
        )}
        <div ref={sentinel} style={{ height: 1 }} />
      </div>
      <aside className="side-col">
        {user ? (
          <div className="me-row">
            <Avatar user={user} size="lg" />
            <div>
              <div className="name">{user.username}</div>
              <div className="sub">{user.full_name}</div>
            </div>
          </div>
        ) : (
          <div className="me-row guest-cta">
            <div>
              <div className="name">Instagram</div>
              <div className="sub">로그인하면 게시하고 좋아요·댓글을 남길 수 있습니다.</div>
              <Link className="btn" to="/login" style={{ width: "auto", marginTop: 10, display: "inline-block" }}>
                로그인
              </Link>
            </div>
          </div>
        )}
        <SuggestedUsers users={suggested} onRemove={removeSuggested} className="suggested-sidebar" />
      </aside>
    </div>
  );
}
