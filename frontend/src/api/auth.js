import client from "./client";

export const login = (username, password) =>
  client.post("/auth/login", { username, password }).then((r) => r.data);

export const signup = (payload) => client.post("/auth/signup", payload).then((r) => r.data);

export const me = () => client.get("/auth/me").then((r) => r.data);

export const changePassword = (current_password, new_password) =>
  client.post("/auth/password", { current_password, new_password }).then((r) => r.data);
