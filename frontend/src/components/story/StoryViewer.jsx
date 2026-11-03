import { useEffect, useState } from "react";
import * as storiesApi from "../../api/stories";
import { useAuth } from "../../context/AuthContext";
import { mediaUrl } from "../../utils/format";

export default function StoryViewer({ groups, startIndex, onClose }) {
  const { user } = useAuth();
  const [gi, setGi] = useState(startIndex || 0);
  const [si, setSi] = useState(0);
  const group = groups[gi];
  const story = group?.stories[si];

  useEffect(() => {
    if (story) storiesApi.viewStory(story.id);
  }, [story?.id]);

  useEffect(() => {
    if (!story) return;
    const t = setTimeout(next, 5000);
    return () => clearTimeout(t);
  }, [gi, si, story?.id]);

  const next = () => {
    if (!group) return onClose();
    if (si + 1 < group.stories.length) setSi(si + 1);
    else if (gi + 1 < groups.length) {
      setGi(gi + 1);
      setSi(0);
    } else onClose();
  };
  const prev = () => {
    if (si > 0) setSi(si - 1);
    else if (gi > 0) {
      setGi(gi - 1);
      setSi(groups[gi - 1].stories.length - 1);
    }
  };

  if (!story) return null;

  return (
    <div className="story-viewer" onClick={onClose}>
      <div className="story-frame" onClick={(e) => e.stopPropagation()}>
        <div className="progress">
          {group.stories.map((s, i) => (
            <span key={s.id} className={i <= si ? "on" : ""} />
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <strong>{group.user.username}</strong>
          <div>
            {group.user.id === user.id && (
              <button
                className="btn danger"
                onClick={async () => {
                  await storiesApi.deleteStory(story.id);
                  onClose();
                }}
              >
                삭제
              </button>
            )}
            <button className="btn ghost" onClick={onClose} style={{ color: "#fff", marginLeft: 8 }}>
              닫기
            </button>
          </div>
        </div>
        <div style={{ position: "relative" }}>
          <img src={mediaUrl(story.media_url)} alt="" />
          <button className="carousel-btn l" onClick={prev}>
            ‹
          </button>
          <button className="carousel-btn r" onClick={next}>
            ›
          </button>
        </div>
      </div>
    </div>
  );
}
