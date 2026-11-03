import client from "./client";

export const stats = () => client.get("/admin/stats").then((r) => r.data);

export const users = (params) => client.get("/admin/users", { params }).then((r) => r.data);

export const deleteUser = (id) => client.delete(`/admin/users/${id}`).then((r) => r.data);

export const posts = (params) => client.get("/admin/posts", { params }).then((r) => r.data);

export const deletePost = (id) => client.delete(`/admin/posts/${id}`).then((r) => r.data);
