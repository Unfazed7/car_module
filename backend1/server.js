// backend/server.js

const { Server } = require("socket.io");

const PORT = 5001;

const io = new Server(PORT, {
  cors: {
    origin: "*", // ⚠️ Allow all for dev. Replace with your frontend origin in production.
    methods: ["GET", "POST"]
  }
});

console.log(`🚀 Socket.IO Server running on http://localhost:${PORT}`);

io.on("connection", (socket) => {
  console.log("🟢 Frontend connected:", socket.id);

  // Relay backend animation events to frontend
  socket.on("frontend_animation", (data) => {
    console.log("📩 Received from backend:", JSON.stringify(data, null, 2));
    io.emit("frontend_animation", data);
  });

  socket.on("disconnect", () => {
    console.log("🔴 Disconnected:", socket.id);
  });
});
