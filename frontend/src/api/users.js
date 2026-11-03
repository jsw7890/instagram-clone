import client from "./client";

export const getUser = (username) => client.get(`/users/${username}`).then((r) => r.data);

export const userPosts = (username, cursor) =>
  client.get(`/users/${username}/posts`, { params: { cursor } }).then((r) => r.data);

export const savedPosts = (username, cursor) =>
  client.get(`/users/${username}/saved`, { params: { cursor } }).then((r) => r.data);

export const follow = (username) => client.post(`/users/${username}/follow`).then((r) => r.data);

export const unfollow = (username) => client.delete(`/users/${username}/follow`).then((r) => r.data);

export const followers = (username) => client.get(`/users/${username}/followers`).then((r) => r.data);

export const following = (username) => client.get(`/users/${username}/following`).then((r) => r.data);

export const suggested = () => client.get("/users/suggested", { params: { limit: 5 } }).then((r) => r.data);

export const updateMe = (payload) => client.patch("/users/me", payload).then((r) => r.data);

export const uploadAvatar = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return client.post("/users/me/avatar", fd).then((r) => r.data);
};

export const searchAll = (q) => client.get("/search", { params: { q } }).then((r) => r.data);

export const getPrivacy = () => client.get("/users/me/privacy").then((r) => r.data);

export const updatePrivacy = (payload) => client.patch("/users/me/privacy", payload).then((r) => r.data);
