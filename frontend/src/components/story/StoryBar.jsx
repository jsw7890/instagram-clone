import { useEffect, useRef, useState } from "react";
import * as storiesApi from "../../api/stories";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { formatApiDetail } from "../../utils/apiError";
import Avatar from "../user/Avatar";
import StoryViewer from "./StoryViewer";

export default function StoryBar() {
  const { user } = useAuth();
  const toast = useToast();
  const [groups, setGroups] = useState([]);
  const [viewer, setViewer] = useState(null);
  const fileRef = useRef();

  const load = () => storiesApi.storyFeed().then((d) => setGroups(d.items || []));
  useEffect(() => {
    load();
  }, []);

  const mine = groups.find((g) => g.user.id === user.id);
  const others = groups.filter((g) => g.user.id !== user.id);

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      await storiesApi.createStory(file);
      load();
    } catch (ex) {
      toast.error(formatApiDetail(ex.response?.data?.detail, "스토리를 올리지 못했습니다"));
    }
  };

  return (
    <>
      <div className="story-bar">
        <button className="story-item" onClick={() => (mine ? setViewer({ groups: [mine, ...others], index: 0 }) : fileRef.current.click())}>
          <Avatar user={user} size="lg" ring seen={!mine} />
          <span>내 스토리</span>
        </button>
        {others.map((g, i) => (
          <button
            key={g.user.id}
            className="story-item"
            onClick={() => setViewer({ groups: [mine, ...others].filter(Boolean), index: mine ? i + 1 : i })}
          >
            <Avatar user={g.user} size="lg" ring seen={!g.has_unseen} />
            <span>{g.user.username}</span>
          </button>
        ))}
        <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={onFile} />
      </div>
      {viewer && (
        <StoryViewer
          groups={viewer.groups}
          startIndex={viewer.index}
          onClose={() => {
            setViewer(null);
            load();
          }}
          onAdd={() => fileRef.current.click()}
        />
      )}
    </>
  );
}
