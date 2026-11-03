import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import * as postsApi from "../api/posts";
import Avatar from "../components/user/Avatar";
import { Bookmark, Heart } from "../components/Icons";
import { useAuth } from "../context/AuthContext";
import useRequireLogin from "../hooks/useRequireLogin";
import { mediaUrl, timeAgo } from "../utils/format";

export default function PostDetailPage() {
  const { postId } = useParams();
  const { user } = useAuth();
  const requireLogin = useRequireLogin();
  const nav = useNavigate();
  const [post, setPost] = useState(undefined);
  const [comments, setComments] = useState([]);
  const [text, setText] = useState("");
  const [idx, setIdx] = useState(0);

  const load = async () => {
    try {
      const p = await postsApi.getPost(postId);
      setPost(p);
      setComments((await postsApi.comments(postId)).items);
    } catch {
      setPost(null);
    }
  };
  useEffect(() => {
    setPost(undefined);
    setComments([]);
    load();
  }, [postId]);

  if (post === null) return <Navigate to="/not-found" replace />;
  if (post === undefined) return <div className="spinner" />;
  const img = post.images[idx];

  const toggleLike = async () => {
    if (!requireLogin()) return;
    const liked = post.liked;
    setPost({ ...post, liked: !liked, likes_count: post.likes_count + (liked ? -1 : 1) });
    if (liked) await postsApi.unlikePost(post.id);
    else await postsApi.likePost(post.id);
  };

  return (
    <div className="detail">
      <div className="detail-media">
        {img && <img src={mediaUrl(img.url)} alt="" />}
        {post.images.length > 1 && (
          <>
            {idx > 0 && (
              <button className="carousel-btn l" onClick={() => setIdx(idx - 1)}>
                ‹
              </button>
            )}
            {idx < post.images.length - 1 && (
              <button className="carousel-btn r" onClick={() => setIdx(idx + 1)}>
                ›
              </button>
            )}
          </>
        )}
      </div>
      <div className="detail-side">
        <div className="post-head">
          <Link to={`/${post.author.username}`}>
            <Avatar user={post.author} />
          </Link>
          <Link to={`/${post.author.username}`} style={{ fontWeight: 600 }}>
            {post.author.username}
          </Link>
          {user && post.author.id === user.id && (
            <button
              className="btn danger"
              onClick={async () => {
                if (!confirm("삭제할까요?")) return;
                await postsApi.deletePost(post.id);
                nav("/");
              }}
            >
              삭제
            </button>
          )}
        </div>
        <div className="detail-comments">
          {post.caption && (
            <div className="user-row">
              <Avatar user={post.author} />
              <div>
                <strong>{post.author.username}</strong> {post.caption}
              </div>
            </div>
          )}
          {comments.map((c) => (
            <div className="user-row" key={c.id}>
              <Avatar user={c.author} />
              <div style={{ flex: 1 }}>
                <strong>{c.author.username}</strong> {c.body}
                <div className="muted">{timeAgo(c.created_at)}</div>
              </div>
              {user && (c.author.id === user.id || post.author.id === user.id) && (
                <button
                  className="btn ghost"
                  onClick={async () => {
                    await postsApi.deleteComment(c.id);
                    setComments(comments.filter((x) => x.id !== c.id));
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="post-actions">
          <button className={`icon-btn ${post.liked ? "liked" : ""}`} onClick={toggleLike}>
            <Heart filled={post.liked} />
          </button>
          <span style={{ flex: 1 }} />
          <button
            className="icon-btn"
            onClick={async () => {
              if (!requireLogin()) return;
              const saved = post.saved;
              setPost({ ...post, saved: !saved });
              if (saved) await postsApi.unsavePost(post.id);
              else await postsApi.savePost(post.id);
            }}
          >
            <Bookmark filled={post.saved} />
          </button>
        </div>
        <div className="post-body">
          <strong>좋아요 {post.likes_count}개</strong>
          <div className="muted">{timeAgo(post.created_at)}</div>
        </div>
        <form
          className="comment-form"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!requireLogin()) return;
            if (!text.trim()) return;
            const c = await postsApi.addComment(post.id, text.trim());
            setComments([...comments, c]);
            setText("");
          }}
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onFocus={() => {
              if (!user) requireLogin();
            }}
            placeholder={user ? "댓글 달기..." : "댓글을 달려면 로그인하세요"}
          />
          <button type="submit">게시</button>
        </form>
      </div>
    </div>
  );
}
