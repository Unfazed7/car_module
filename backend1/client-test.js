const io = require("socket.io-client");
const socket = io("http://localhost:5001");

socket.on("connect", () => {
  console.log("✅ Test client connected");
  socket.emit("frontend_animation", {
    animations: ["hoodAction"],
    reverse: false
  });
  console.log("📤 Test message sent");
});
