import { useState } from "react";
import { Link } from "react-router-dom";
import * as postsApi from "../../api/posts";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import useRequireLogin from "../../hooks/useRequireLogin";
import { mediaUrl, timeAgo } from "../../utils/format";
import { Bookmark, Comment, Heart, Send } from "../Icons";
import Avatar from "../user/Avatar";

export default function PostCard({ post, onDeleted }) {
  const { user } = useAuth();
  const requireLogin = useRequireLogin();
  const toast = useToast();
  const [data, setData] = useState(post);
  const [idx, setIdx] = useState(0);
  const [captionOpen, setCaptionOpen] = useState(false);
  const [text, setText] = useState("");

  const img = data.images[idx];
  const caption = data.caption || "";
  const short = caption.length > 125 && !captionOpen;

  const toggleLike = async () => {
    if (!requireLogin()) return;
    const liked = data.liked;
    setData({ ...data, liked: !liked, likes_count: data.likes_count + (liked ? -1 : 1) });
    try {
      if (liked) await postsApi.unlikePost(data.id);
      else await postsApi.likePost(data.id);
    } catch {
      setData(data);
    }
  };

  const toggleSave = async () => {
    if (!requireLogin()) return;
    const saved = data.saved;
    setData({ ...data, saved: !saved });
    try {
      if (saved) await postsApi.unsavePost(data.id);
      else await postsApi.savePost(data.id);
    } catch {
      setData(data);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!requireLogin()) return;
    if (!text.trim()) return;
    try {
      await postsApi.addComment(data.id, text.trim());
      setData({ ...data, comments_count: data.comments_count + 1 });
      setText("");
    } catch {
      toast.error("댓글을 작성하지 못했습니다");
    }
  };

  const copyLink = async () => {
    await navigator.clipboard.writeText(`${window.location.origin}/p/${data.id}`);
    toast.success("링크를 복사했습니다");
  };

  const remove = async () => {
    if (!confirm("게시물을 삭제할까요?")) return;
    await postsApi.deletePost(data.id);
    onDeleted?.(data.id);
  };

  return (
    <article className="post-card">
      <div className="post-head">
        <Link to={`/${data.author.username}`}>
          <Avatar user={data.author} />
        </Link>
        <div style={{ flex: 1 }}>
          <Link to={`/${data.author.username}`} className="name" style={{ fontWeight: 600 }}>
            {data.author.username}
          </Link>
          {data.location && <div className="muted">{data.location}</div>}
        </div>
        {data.author.id === user?.id && (
          <button className="btn danger" onClick={remove}>
            삭제
          </button>
        )}
      </div>
      <div className="post-media">
        {img && <img src={mediaUrl(img.url)} alt="" />}
        {data.images.length > 1 && (
          <>
            {idx > 0 && (
              <button className="carousel-btn l" onClick={() => setIdx(idx - 1)}>
                ‹
              </button>
            )}
            {idx < data.images.length - 1 && (
              <button className="carousel-btn r" onClick={() => setIdx(idx + 1)}>
                ›
              </button>
            )}
          </>
        )}
      </div>
      {data.images.length > 1 && (
        <div className="dots">
          {data.images.map((_, i) => (
            <i key={i} className={i === idx ? "on" : ""} />
          ))}
        </div>
      )}
      <div className="post-actions">
        <button className={`icon-btn ${data.liked ? "liked" : ""}`} aria-label="좋아요" onClick={toggleLike}>
          <Heart filled={data.liked} />
        </button>
        <Link className="icon-btn" to={`/p/${data.id}`} aria-label="댓글">
          <Comment />
        </Link>
        <button className="icon-btn" aria-label="공유" onClick={copyLink}>
          <Send />
        </button>
        <span style={{ flex: 1 }} />
        <button className="icon-btn" aria-label="저장" onClick={toggleSave}>
          <Bookmark filled={data.saved} />
        </button>
      </div>
      <div className="post-body">
        <div style={{ fontWeight: 600 }}>좋아요 {data.likes_count.toLocaleString()}개</div>
        {caption && (
          <p className="caption">
            <Link to={`/${data.author.username}`} style={{ fontWeight: 600, marginRight: 6 }}>
              {data.author.username}
            </Link>
            {short ? `${caption.slice(0, 125)}...` : caption}{" "}
            {caption.length > 125 && (
              <button className="more" onClick={() => setCaptionOpen(!captionOpen)}>
                {captionOpen ? "접기" : "더 보기"}
              </button>
            )}
          </p>
        )}
        {data.comments_count > 0 && (
          <Link className="comment-preview" to={`/p/${data.id}`}>
            댓글 {data.comments_count}개 모두 보기
          </Link>
        )}
        <div className="muted">{timeAgo(data.created_at)}</div>
      </div>
      <form className="comment-form" onSubmit={submit}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onFocus={() => {
            if (!user) requireLogin();
          }}
          placeholder={user ? "댓글 달기..." : "댓글을 달려면 로그인하세요"}
        />
        <button type="submit" disabled={!text.trim()}>
          게시
        </button>
      </form>
    </article>
  );
}
