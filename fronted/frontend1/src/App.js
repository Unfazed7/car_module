import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import CarViewer from './components/CarViewer';
import { io } from 'socket.io-client';

// 💡 Use socket reference to avoid re-binding
const socket = io("http://localhost:5001", {
  transports: ['websocket'],
  reconnectionAttempts: 5
});

const buttons = [
  { label: 'Engine ON', command: 'engine_on' },
  { label: 'Engine OFF', command: 'engine_off' },
  { label: 'Bonnet OPEN', command: 'bonnet_open' },
  { label: 'Bonnet CLOSE', command: 'bonnet_close' },
  { label: 'Driver Door OPEN', command: 'door_open' },
  { label: 'Driver Door CLOSE', command: 'door_close' },
  { label: 'Headlamp ON', command: 'headlamp_on' },
  { label: 'Headlamp OFF', command: 'headlamp_off' },
  { label: 'Drive Forward', command: 'tire_spin' },
  { label: 'Brake', command: 'brake_apply' }
];

function App() {
  const [activeCommand, setActiveCommand] = useState(null);
  const [animations, setAnimations] = useState([]);
  const [reverse, setReverse] = useState(false);
  const [engineOn, setEngineOn] = useState(false);

  useEffect(() => {
    toast.info("🚀 CAN Dashboard Ready!", { autoClose: 1500 });

    // ✅ Socket Event Handlers
    const onAnimation = (data) => {
      console.log("📩 Received CAN-triggered animation:", data);
      const animNames = (data.animations || []).map(a =>
        typeof a === 'string' ? a : a?.name
      ).filter(Boolean);

      if (animNames.length > 0) {
        setAnimations(animNames);
        setReverse(data.reverse);
        console.log("🎬 Triggering animations:", animNames);

        setTimeout(() => {
          setAnimations([]);
          setReverse(false);
        }, 2000);
      } else {
        console.warn("⚠️ Received empty animation list.");
      }
    };

    const onSecurityAlert = (alert) => {
      console.log("🚨 SECURITY ALERT:", alert);

      if (alert.type === "replay_attack") {
        toast.error(`🔁 Replay Attack!\nCAN ID: ${alert.can_id}, Counter: ${alert.counter}`, {
          autoClose: 6000
        });
      } else if (alert.type === "tamper_detected") {
        toast.error(`🛑 Tampering Detected: ${alert.error}`, {
          autoClose: 6000
        });
      }
    };

    const onConnect = () => console.log("✅ Socket connected");
    const onDisconnect = () => console.warn("🔌 Socket disconnected");
    const onError = (e) => console.error("❌ Socket Error:", e.message);

    socket.on("connect", onConnect);
    socket.on("frontend_animation", onAnimation);
    socket.on("security_alert", onSecurityAlert);
    socket.on("disconnect", onDisconnect);
    socket.on("connect_error", onError);

    // 🧼 Cleanup to avoid multiple bindings
    return () => {
      socket.off("connect", onConnect);
      socket.off("frontend_animation", onAnimation);
      socket.off("security_alert", onSecurityAlert);
      socket.off("disconnect", onDisconnect);
      socket.off("connect_error", onError);
    };
  }, []);

  const sendCANMessage = async (command, label) => {
    setActiveCommand(command);
    toast.info(`📤 Sending "${label}"`, { autoClose: 800 });

    try {
      await axios.get(`http://localhost:5000/send/${command}`);
      toast.success(`✅ "${label}" sent!`);
    } catch {
      toast.error(`❌ Failed to send "${label}"`);
    }

    setTimeout(() => setActiveCommand(null), 1200);
  };

  const handleClick = async (btn) => {
    if (!engineOn && btn.command !== 'engine_on') {
      toast.warning("⚠️ Start the engine first!");
      return;
    }

    await sendCANMessage(btn.command, btn.label);

    if (btn.command === 'engine_on') setEngineOn(true);
    if (btn.command === 'engine_off') setEngineOn(false);
  };

  return (
    <div className="main-container">
      <ToastContainer position="bottom-right" />
      <div className="left-panel">
        <h1 className="title">CAN Control Panel</h1>
        <div className="button-list">
          {buttons.map((btn) => (
            <button
              key={btn.command}
              className={`action-button ${activeCommand === btn.command ? 'flash' : ''}`}
              onClick={() => handleClick(btn)}
              disabled={!engineOn && btn.command !== 'engine_on'}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      <div className="right-panel">
        <CarViewer animations={animations} reverse={reverse} />
      </div>
    </div>
  );
}

export default App;
