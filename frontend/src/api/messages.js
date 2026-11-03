import client from "./client";

export const conversations = () => client.get("/conversations").then((r) => r.data);

export const openConversation = (username) =>
  client.post("/conversations", { username }).then((r) => r.data);

export const messages = (id, cursor) =>
  client.get(`/conversations/${id}/messages`, { params: { cursor } }).then((r) => r.data);

export const sendMessage = (id, body) =>
  client.post(`/conversations/${id}/messages`, { body }).then((r) => r.data);

export const readConversation = (id) => client.post(`/conversations/${id}/read`).then((r) => r.data);
