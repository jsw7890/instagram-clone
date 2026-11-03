import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import * as msgApi from "../api/messages";
import * as usersApi from "../api/users";
import Avatar from "../components/user/Avatar";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { formatApiDetail } from "../utils/apiError";
import { timeAgo } from "../utils/format";

function ConversationList() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState([]);
  const nav = useNavigate();

  useEffect(() => {
    msgApi.conversations().then(setItems);
  }, []);

  useEffect(() => {
    if (q.length < 1) {
      setHits([]);
      return;
    }
    usersApi.searchAll(q).then((d) => setHits(d.users));
  }, [q]);

  return (
    <div className="dm-list">
      <h3>메시지</h3>
      <div style={{ padding: "0 12px 12px" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="새 메시지 상대 검색"
          style={{ width: "100%", padding: 8, border: "1px solid var(--border)", borderRadius: 8 }}
        />
        {hits.map((u) => (
          <button
            key={u.id}
            className="user-row"
            style={{ width: "100%", background: "none", border: 0, padding: "8px 0" }}
            onClick={async () => {
              const c = await msgApi.openConversation(u.username);
              nav(`/direct/${c.id}`);
            }}
          >
            <Avatar user={u} />
            <span className="name">{u.username}</span>
          </button>
        ))}
      </div>
      {items.map((c) => (
        <Link
          key={c.id}
          to={`/direct/${c.id}`}
          className={`user-row ${c.unread_count ? "unread" : ""}`}
          style={{ padding: 12 }}
        >
          <Avatar user={c.other_user} size="lg" />
          <div className="meta">
            <div className="name">{c.other_user?.username}</div>
            <div className="sub">
              {c.last_message?.body} · {c.last_message ? timeAgo(c.last_message.created_at) : ""}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

export function DirectListPage() {
  return (
    <div className="dm">
      <ConversationList />
      <div className="empty">대화를 선택하세요</div>
    </div>
  );
}

export function DirectThreadPage() {
  const { conversationId } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const [meta, setMeta] = useState(null);
  const [items, setItems] = useState([]);
  const [text, setText] = useState("");

  const load = async () => {
    const convs = await msgApi.conversations();
    setMeta(convs.find((c) => String(c.id) === String(conversationId)));
    const msgs = await msgApi.messages(conversationId);
    setItems(msgs.items);
    await msgApi.readConversation(conversationId);
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [conversationId]);

  return (
    <div className="dm">
      <ConversationList />
      <div className="dm-thread">
        <div className="post-head">
          {meta?.other_user && (
            <>
              <Avatar user={meta.other_user} />
              <strong>{meta.other_user.username}</strong>
            </>
          )}
        </div>
        <div className="bubbles">
          {items.map((m) => (
            <div key={m.id} className={`bubble ${m.sender_id === user.id ? "me" : ""}`}>
              {m.body}
            </div>
          ))}
        </div>
        <form
          className="comment-form"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!text.trim()) return;
            try {
              const msg = await msgApi.sendMessage(conversationId, text.trim());
              setItems([...items, msg]);
              setText("");
            } catch (ex) {
              toast.error(formatApiDetail(ex.response?.data?.detail, "메시지를 보내지 못했습니다"));
            }
          }}
        >
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="메시지 입력..." />
          <button type="submit">보내기</button>
        </form>
      </div>
    </div>
  );
}
