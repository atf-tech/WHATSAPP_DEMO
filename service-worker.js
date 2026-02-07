self.addEventListener("push", function (event) {
  if (!event.data) return;

  const data = event.data.json();

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/static/img/whatsapp.png",
      badge: "/static/img/whatsapp.png",
      data: {
        conversation_id: data.conversation_id
      }
    })
  );

  // 🔊 Tell all open tabs to play sound
  self.clients.matchAll({ includeUncontrolled: true }).then(clients => {
    clients.forEach(client => {
      client.postMessage({ type: "PLAY_SOUND" });
    });
  });
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();

  event.waitUntil(
    clients.openWindow("/chat/inbox/")
  );
});
