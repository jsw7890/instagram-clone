import client from "./client";

export const feed = (cursor) =>
  client.get("/posts/feed", { params: { cursor, limit: 10 } }).then((r) => r.data);

export const explore = (cursor) =>
  client.get("/posts/explore", { params: { cursor, limit: 18 } }).then((r) => r.data);

export const getPost = (id) => client.get(`/posts/${id}`).then((r) => r.data);

export const createPost = (formData) => client.post("/posts", formData).then((r) => r.data);

export const deletePost = (id) => client.delete(`/posts/${id}`).then((r) => r.data);

export const likePost = (id) => client.post(`/posts/${id}/like`).then((r) => r.data);

export const unlikePost = (id) => client.delete(`/posts/${id}/like`).then((r) => r.data);

export const savePost = (id) => client.post(`/posts/${id}/save`).then((r) => r.data);

export const unsavePost = (id) => client.delete(`/posts/${id}/save`).then((r) => r.data);

export const comments = (id, cursor) =>
  client.get(`/posts/${id}/comments`, { params: { cursor } }).then((r) => r.data);

export const addComment = (id, body) =>
  client.post(`/posts/${id}/comments`, { body }).then((r) => r.data);

export const deleteComment = (id) => client.delete(`/comments/${id}`).then((r) => r.data);
