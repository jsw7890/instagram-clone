import { useEffect, useRef, useState } from "react";
import * as postsApi from "../api/posts";
import PostGrid from "../components/post/PostGrid";

export default function ExplorePage() {
  const [items, setItems] = useState([]);
  const [cursor, setCursor] = useState(undefined);
  const [loading, setLoading] = useState(true);
  const sentinel = useRef();

  const load = async (c) => {
    const data = await postsApi.explore(c || undefined);
    setItems((prev) => (c ? [...prev, ...data.items] : data.items));
    setCursor(data.next_cursor);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!sentinel.current) return;
    const io = new IntersectionObserver((ents) => {
      if (ents[0].isIntersecting && cursor) load(cursor);
    });
    io.observe(sentinel.current);
    return () => io.disconnect();
  }, [cursor]);

  return (
    <div className="profile">
      <PostGrid items={items} />
      {loading && <div className="spinner" />}
      <div ref={sentinel} style={{ height: 1 }} />
    </div>
  );
}
