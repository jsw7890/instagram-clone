import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as postsApi from "../../api/posts";
import { useToast } from "../../context/ToastContext";
import { formatApiDetail } from "../../utils/apiError";
import Modal from "../common/Modal";

export default function CreatePost({ onClose }) {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [caption, setCaption] = useState("");
  const [location, setLocation] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const nav = useNavigate();

  const pick = (e) => {
    const list = [...e.target.files].slice(0, 10);
    setFiles(list);
    setPreviews(list.map((f) => URL.createObjectURL(f)));
  };

  const share = async () => {
    if (!files.length) return;
    setBusy(true);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      fd.append("caption", caption);
      fd.append("location", location);
      const post = await postsApi.createPost(fd);
      toast.success("게시했습니다");
      onClose();
      nav(`/p/${post.id}`);
    } catch (ex) {
      toast.error(formatApiDetail(ex.response?.data?.detail, "게시에 실패했습니다"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="새 게시물 만들기" onClose={onClose} wide>
      <div style={{ padding: 16 }}>
        {!files.length ? (
          <label className="empty" style={{ display: "block", cursor: "pointer" }}>
            사진을 선택하세요
            <input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden onChange={pick} />
          </label>
        ) : (
          <>
            <img className="create-preview" src={previews[0]} alt="" />
            <textarea rows={4} maxLength={2200} placeholder="문구..." value={caption} onChange={(e) => setCaption(e.target.value)} />
            <input type="text" maxLength={100} placeholder="위치 (선택)" value={location} onChange={(e) => setLocation(e.target.value)} />
            <button className="btn" disabled={busy} onClick={share}>
              공유하기
            </button>
          </>
        )}
      </div>
    </Modal>
  );
}
