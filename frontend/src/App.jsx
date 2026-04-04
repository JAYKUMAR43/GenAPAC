import React, { useState, useRef, useEffect } from 'react';

const API_BASE = "https://genapac.onrender.com";

console.log("Current API Base:", API_BASE);

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatBoxRef = useRef(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  // Auto-poll notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await fetch(`${API_BASE}/notifications`);
        const data = await response.json();
        if (data.notifications && data.notifications.length > 0) {
          setNotifications(prev => {
            // avoid duplicates
            const newNotifs = data.notifications.filter(n => !prev.find(p => p.id === n.id));
            return [...prev, ...newNotifs];
          });
          // Mark read
          for (let n of data.notifications) {
            await fetch(`${API_BASE}/notifications/mark_read`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ notification_id: n.id })
            });
          }
        }
      } catch (e) {
        console.error("Failed fetching notifications", e);
      }
    };
    const intervalId = setInterval(fetchNotifications, 5000);
    return () => clearInterval(intervalId);
  }, []);

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const addMessage = (role, text, intent = null) => {
    setMessages(prev => [...prev, { role, text, intent }]);
  };

  const handleSendText = async () => {
    if (!inputText.trim()) return;

    // Add user message
    const msg = inputText;
    addMessage('user', msg);
    setInputText("");
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('message', msg);

      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      addMessage('bot', data.response, data.intent);

      if (data.audio_url) {
        playAudio(data.audio_url);
      }
    } catch (error) {
      addMessage('bot', 'Failed to connect to the server.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSendText();
    }
  };

  const handleMicClick = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const startRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert("Audio recording not supported by this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        sendVoiceData(audioBlob);

        // Cleanup stream
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone", err);
      alert("Could not access microphone.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceData = async (audioBlob) => {
    setIsLoading(true);
    addMessage('user', '🎤 [Voice Message]');
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'record.webm');

      const response = await fetch(`${API_BASE}/voice`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      // Update the user's voice message with recognized text
      if (data.user_text_detected) {
        setMessages(prev => {
          const newMsg = [...prev];
          newMsg[newMsg.length - 1].text = `🎤 ${data.user_text_detected}`;
          return newMsg;
        });
      }

      addMessage('bot', data.response, data.intent);

      if (data.audio_url) {
        playAudio(data.audio_url);
      }
    } catch (error) {
      addMessage('bot', 'Failed to upload voice recording.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (text) => {
    setInputText(text);
  };

  const playAudio = (path) => {
    const audio = new Audio(`${API_BASE}${path}`);
    audio.play().catch(e => console.error("Error playing audio:", e));
  };

  return (
    <div className="app-container">
      <div className="toast-container">
        {notifications.map((n) => (
          <div key={n.id} className="toast" onClick={() => dismissNotification(n.id)}>
            🔔 {n.message}
          </div>
        ))}
      </div>
      <div className="header">
        <h1>AI Productivity Assistant (v2)</h1>
      </div>


      <div className="chat-box" ref={chatBoxRef}>
        {messages.length === 0 && !isLoading && (
          <div className="empty-state">
            <h2>How can I assist you today?</h2>
            <div className="suggestions-grid">
              <button className="suggest-btn" onClick={() => handleSuggestionClick("Schedule a meeting tomorrow at 10 AM")}>📅 Schedule Meeting</button>
              <button className="suggest-btn" onClick={() => handleSuggestionClick("Add a task to buy groceries")}>✅ Add Task</button>
              <button className="suggest-btn" onClick={() => handleSuggestionClick("Save a note about my new startup idea")}>📝 Save Note</button>
              <button className="suggest-btn" onClick={() => handleSuggestionClick("Mere saare tasks dikhao")}>🔍 List Tasks</button>
            </div>
          </div>
        )}
        {messages.map((m, idx) => (
          <div key={idx} className={`message ${m.role}`}>
            {m.text}
            {m.intent && m.intent !== "unknown" && m.intent !== "error" && (
              <div className="bot-intent">INTENT: {m.intent}</div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message bot">
            <div className="typing-dots"><span></span><span></span><span></span></div>
          </div>
        )}
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder="Ask me to schedule a meeting or save a task..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || isRecording}
        />
        <button onClick={handleMicClick} className={isRecording ? 'recording' : ''} disabled={isLoading}>
          {isRecording ? '🛑' : '🎤'}
        </button>
        <button onClick={handleSendText} disabled={isLoading || isRecording || !inputText.trim()}>
          ➤
        </button>
      </div>
    </div>
  );
}

export default App;
