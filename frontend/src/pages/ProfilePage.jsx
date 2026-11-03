import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import * as usersApi from "../api/users";
import Modal from "../components/common/Modal";
import PostGrid from "../components/post/PostGrid";
import Avatar from "../components/user/Avatar";
import FollowButton from "../components/user/FollowButton";
import ProfileMessageButton from "../components/user/ProfileMessageButton";
import { Gear } from "../components/Icons";
import { useAuth } from "../context/AuthContext";

export default function ProfilePage({ savedOnly }) {
  const { username } = useParams();
  const { refreshMe, logout } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [list, setList] = useState(null);
  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({ full_name: "", bio: "", website: "" });
  const [missing, setMissing] = useState(false);

  const load = async () => {
    try {
      const p = await usersApi.getUser(username);
      setProfile(p);
      setForm({ full_name: p.full_name || "", bio: p.bio || "", website: p.website || "" });
      const grid = savedOnly ? await usersApi.savedPosts(username) : await usersApi.userPosts(username);
      setPosts(grid.items);
    } catch {
      setMissing(true);
    }
  };

  useEffect(() => {
    setMissing(false);
    load();
  }, [username, savedOnly]);

  if (missing) return <Navigate to="/not-found" replace />;
  if (!profile) return <div className="spinner" />;
  if (savedOnly && !profile.is_me) return <Navigate to={`/${username}`} replace />;

  const openList = async (kind) => {
    const data = kind === "followers" ? await usersApi.followers(username) : await usersApi.following(username);
    setList({ title: kind === "followers" ? "팔로워" : "팔로잉", items: data.items });
  };

  return (
    <div className="profile">
      <header className="profile-head">
        <Avatar user={profile} size="xl" />
        <div className="profile-meta">
          <div className="row profile-title-row">
            <h2>{profile.username}</h2>
            {profile.is_me ? (
              <>
                <Link to="/settings" className="icon-btn profile-settings-gear" aria-label="설정">
                  <Gear />
                </Link>
                <button className="btn" style={{ background: "#efefef", color: "#262626", width: "auto" }} onClick={() => setEdit(true)}>
                  프로필 편집
                </button>
              </>
            ) : (
              <div className="profile-actions">
                <FollowButton user={profile} onChange={() => load()} />
                <ProfileMessageButton username={profile.username} />
              </div>
            )}
          </div>
          <ul>
            <li>
              게시물 <strong>{profile.posts_count}</strong>
            </li>
            <li>
              <button onClick={() => openList("followers")}>
                팔로워 <strong>{profile.followers_count}</strong>
              </button>
            </li>
            <li>
              <button onClick={() => openList("following")}>
                팔로잉 <strong>{profile.following_count}</strong>
              </button>
            </li>
          </ul>
          <div style={{ fontWeight: 600 }}>{profile.full_name}</div>
          <div>{profile.bio}</div>
        </div>
      </header>
      {profile.is_me && (
        <div className="profile-mobile-actions">
          <Link className="btn profile-mobile-btn" to="/settings">
            설정
          </Link>
          <button
            type="button"
            className="btn profile-mobile-btn"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            로그아웃
          </button>
        </div>
      )}
      <div className="tabs">
        <Link className={!savedOnly ? "on" : ""} to={`/${username}`}>
          게시물
        </Link>
        {profile.is_me && (
          <Link className={savedOnly ? "on" : ""} to={`/${username}/saved`}>
            저장됨
          </Link>
        )}
        {profile.is_me && (
          <Link className="profile-tab-settings" to="/settings">
            설정
          </Link>
        )}
      </div>
      <PostGrid items={posts} />
      {list && (
        <Modal title={list.title} onClose={() => setList(null)}>
          <div style={{ padding: 12 }}>
            {list.items.map((u) => (
              <Link key={u.id} to={`/${u.username}`} className="user-row" onClick={() => setList(null)}>
                <Avatar user={u} />
                <div>
                  <div className="name">{u.username}</div>
                  <div className="sub">{u.full_name}</div>
                </div>
              </Link>
            ))}
          </div>
        </Modal>
      )}
      {edit && (
        <Modal title="프로필 편집" onClose={() => setEdit(false)}>
          <div style={{ padding: 16 }}>
            <input type="file" accept="image/*" onChange={async (e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              await usersApi.uploadAvatar(f);
              await refreshMe();
              load();
            }} />
            <input type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="성명" />
            <textarea value={form.bio} maxLength={150} onChange={(e) => setForm({ ...form, bio: e.target.value })} placeholder="소개" />
            <input type="text" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} placeholder="웹사이트" />
            <button
              className="btn"
              onClick={async () => {
                await usersApi.updateMe(form);
                await refreshMe();
                setEdit(false);
                load();
              }}
            >
              저장
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
