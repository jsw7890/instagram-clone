import client from "./client";

export const storyFeed = () => client.get("/stories/feed").then((r) => r.data);

export const createStory = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return client.post("/stories", fd).then((r) => r.data);
};

export const viewStory = (id) => client.post(`/stories/${id}/view`).then((r) => r.data);

export const deleteStory = (id) => client.delete(`/stories/${id}`).then((r) => r.data);
