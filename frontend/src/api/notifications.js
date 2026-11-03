import client from "./client";

export const listNotifications = () => client.get("/notifications").then((r) => r.data);

export const readNotifications = () => client.post("/notifications/read").then((r) => r.data);

export const deleteNotification = (id) => client.delete(`/notifications/${id}`).then((r) => r.data);
