import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaCalendarAlt, FaCheckSquare, FaStickyNote, FaListUl, FaMicrophone, FaPaperPlane, FaStop } from 'react-icons/fa';

const API_BASE = "https://genapac.onrender.com";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatEndRef = useRef(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Auto-poll notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await fetch(`${API_BASE}/notifications`);
        const data = await response.json();
        if (data.notifications && data.notifications.length > 0) {
          setNotifications(prev => {
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
        // Handle silently
      }
    };
    const intervalId = setInterval(fetchNotifications, 5000);
    return () => clearInterval(intervalId);
  }, []);

  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const addMessage = (role, text, intent = null) => {
    setMessages(prev => [...prev, { id: Date.now(), role, text, intent }]);
  };

  const handleSendText = async () => {
    if (!inputText.trim()) return;
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
      if (data.audio_url) playAudio(data.audio_url);
    } catch (error) {
      addMessage('bot', 'Failed to connect to the server.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSendText();
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
      alert("Audio recording not supported.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        sendVoiceData(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
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
    const tempId = Date.now();
    setMessages(prev => [...prev, { id: tempId, role: 'user', text: '🎤 [Recording...]' }]);
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'record.webm');
      const response = await fetch(`${API_BASE}/voice`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      setMessages(prev => prev.map(m => m.id === tempId ? { ...m, text: `🎤 ${data.user_text_detected || "Audio"}` } : m));
      addMessage('bot', data.response, data.intent);
      if (data.audio_url) playAudio(data.audio_url);
    } catch (error) {
      setMessages(prev => prev.map(m => m.id === tempId ? { ...m, text: `🎤 Audio Failed` } : m));
      addMessage('bot', 'Failed to upload voice recording.');
    } finally {
      setIsLoading(false);
    }
  };

  const playAudio = (path) => {
    const audio = new Audio(`${API_BASE}${path}`);
    audio.play().catch(e => console.error("Error playing audio:", e));
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0d1117] to-[#04080e] text-[#e6edf3] font-sans overflow-hidden flex justify-center items-center relative">
      
      {/* Toast Container */}
      <div className="absolute top-4 right-4 z-50 flex flex-col gap-3">
        <AnimatePresence>
          {notifications.map((n) => (
            <motion.div
              key={n.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
              className="bg-blue-600/90 text-white px-5 py-3 rounded-xl shadow-lg border border-blue-400/30 backdrop-blur-md cursor-pointer flex items-center gap-3"
              onClick={() => dismissNotification(n.id)}
            >
              <div className="bg-blue-500 rounded-full w-2 h-2 animate-pulse"></div>
              <span className="font-semibold text-sm">{n.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="w-full max-w-3xl h-[100dvh] sm:h-[90vh] bg-black/40 backdrop-blur-2xl sm:border border-white/5 sm:rounded-3xl shadow-2xl flex flex-col relative sm:mx-4 overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-5 border-b border-white/5 bg-white/5 backdrop-blur-md flex items-center justify-center relative">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight">AI Productivity Assistant</h1>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col gap-4">
          {messages.length === 0 && !isLoading && (
             <motion.div 
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ duration: 0.5 }}
               className="m-auto flex flex-col items-center justify-center text-center opacity-80"
             >
                <div className="w-16 h-16 bg-gradient-to-tr from-blue-500 to-indigo-500 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-blue-500/20">
                    <span className="text-3xl text-white">✨</span>
                </div>
                <h2 className="text-2xl font-light mb-8 text-white/90">How can I assist you today?</h2>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-lg">
                  {[
                    { icon: FaCalendarAlt, label: "Schedule Meeting", text: "Schedule a meeting tomorrow at 10 AM", color: "text-blue-400" },
                    { icon: FaCheckSquare, label: "Add Task", text: "Add a task to buy groceries", color: "text-emerald-400" },
                    { icon: FaStickyNote, label: "Save Note", text: "Save a note about my startup idea", color: "text-amber-400" },
                    { icon: FaListUl, label: "List Tasks", text: "List all my tasks", color: "text-purple-400" }
                  ].map((btn, idx) => (
                    <motion.button 
                      key={idx}
                      whileHover={{ scale: 1.03, y: -2 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => setInputText(btn.text)}
                      className="flex items-center gap-3 p-4 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 rounded-2xl transition-colors text-left"
                    >
                      <btn.icon className={`text-xl ${btn.color}`} />
                      <span className="text-sm font-medium text-white/80">{btn.label}</span>
                    </motion.button>
                  ))}
                </div>
             </motion.div>
          )}

          {/* Chat Messages */}
          <AnimatePresence>
            {messages.map((m) => (
              <motion.div 
                key={m.id}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`max-w-[85%] rounded-2xl px-5 py-3.5 shadow-md ${
                  m.role === 'user' 
                  ? 'self-end bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-sm' 
                  : 'self-start bg-white/5 border border-white/10 text-white/90 rounded-bl-sm backdrop-blur-md'
                }`}
              >
                <div className="text-[0.95rem] leading-relaxed whitespace-pre-wrap">{m.text}</div>
                {m.intent && m.intent !== "unknown" && m.intent !== "error" && (
                   <div className="mt-2 text-[0.65rem] tracking-wider uppercase opacity-50 bg-black/20 p-1.5 rounded-lg w-fit">
                     INTENT: {m.intent}
                   </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
             <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               className="self-start px-5 py-4 bg-white/5 border border-white/10 rounded-2xl rounded-bl-sm backdrop-blur-md"
             >
                <div className="flex gap-1.5 items-center justify-center p-1">
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0 }} className="w-1.5 h-1.5 bg-white/60 rounded-full" />
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.2 }} className="w-1.5 h-1.5 bg-white/60 rounded-full" />
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.4 }} className="w-1.5 h-1.5 bg-white/60 rounded-full" />
                </div>
             </motion.div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Sticky Input Area */}
        <div className="p-4 sm:p-5 pb-6 border-t border-white/5 bg-black/20 backdrop-blur-lg z-10 w-full relative">
           <div className="flex items-center gap-2 w-full bg-white/5 focus-within:bg-white/10 transition-colors border border-white/10 focus-within:border-white/20 p-2 rounded-2xl shadow-inner">
             <motion.button 
               whileHover={{ scale: 1.05 }}
               whileTap={{ scale: 0.95 }}
               onClick={handleMicClick} 
               disabled={isLoading}
               className={`w-11 h-11 flex-shrink-0 flex items-center justify-center rounded-xl transition-colors ${
                 isRecording ? 'bg-red-500/20 text-red-400' : 'bg-transparent text-white/50 hover:text-white/80 hover:bg-white/5'
               }`}
             >
               {isRecording ? <FaStop className="animate-pulse" /> : <FaMicrophone />}
             </motion.button>
             
             <input
               type="text"
               value={inputText}
               onChange={(e) => setInputText(e.target.value)}
               onKeyDown={handleKeyDown}
               placeholder="Ask anything..."
               className="flex-1 bg-transparent border-none outline-none text-white/90 placeholder-white/30 px-2 py-2 font-medium"
               disabled={isLoading || isRecording}
             />
             
             <motion.button
               whileHover={inputText.trim() ? { scale: 1.05 } : {}}
               whileTap={inputText.trim() ? { scale: 0.95 } : {}}
               onClick={handleSendText}
               disabled={!inputText.trim() || isLoading || isRecording}
               className="w-11 h-11 flex-shrink-0 flex items-center justify-center bg-blue-600 text-white rounded-xl shadow-lg shadow-blue-600/30 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all"
             >
               <FaPaperPlane className="ml-1" />
             </motion.button>
           </div>
        </div>
      </div>
    </div>
  );
}

export default App;
