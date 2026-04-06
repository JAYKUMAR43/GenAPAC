import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Mic, Square, Paperclip, Calendar, CheckSquare, Folder, ListTodo, ChevronRight, Sparkles } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";

const API_BASE = "https://genapac.onrender.com";

// Spring transition settings
const springTransition = {
  type: "spring",
  stiffness: 250,
  damping: 25,
  mass: 0.5,
  ease: [0.16, 1, 0.3, 1]
};

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const chatEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await fetch(`${API_BASE}/notifications`);
        const data = await response.json();
        if (data.notifications && data.notifications.length > 0) {
          for (let n of data.notifications) {
            const msgLower = n.message.toLowerCase();
            if (msgLower.includes("success") || msgLower.includes("scheduled") || msgLower.includes("done")) {
              toast.success(n.message);
            } else if (msgLower.includes("error") || msgLower.includes("fail")) {
              toast.error(n.message);
            } else {
              toast.success(n.message, { icon: "✨" });
            }
            await fetch(`${API_BASE}/notifications/mark_read`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ notification_id: n.id }),
            });
          }
        }
      } catch (e) {}
    };
    const intervalId = setInterval(fetchNotifications, 5000);
    return () => clearInterval(intervalId);
  }, []);

  const playAudio = (path) => {
    const audio = new Audio(`${API_BASE}${path}`);
    audio.play().catch(() => {});
  };

  const handleSendAction = async (textToSend) => {
    if (!textToSend.trim() || isLoading) return;
    setMessages((prev) => [...prev, { id: Date.now(), role: "user", text: textToSend }]);
    setInput("");
    setIsLoading(true);

    try {
      const historyStr = JSON.stringify(messages.slice(-5).map(m => ({ role: m.role, text: m.text })));
      const formData = new FormData();
      formData.append("message", textToSend);
      formData.append("history", historyStr);
      const response = await fetch(`${API_BASE}/chat`, { method: "POST", body: formData });
      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "ai", text: data.response, intent: data.intent },
      ]);
      if (data.audio_url) playAudio(data.audio_url);
    } catch {
      toast.error("Failed to connect to AI.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSendAction(input);
  };

  const startRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast.error("Audio recording not supported.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        sendVoiceData(audioBlob);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      toast.error("Could not access microphone.");
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
    setMessages((prev) => [...prev, { id: tempId, role: "user", text: "🎤 Processing audio..." }]);
    
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "record.webm");
      const response = await fetch(`${API_BASE}/voice`, { method: "POST", body: formData });
      const data = await response.json();

      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, text: `🎤 ${data.user_text_detected || "Audio"}` } : m))
      );
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "ai", text: data.response, intent: data.intent },
      ]);
      if (data.audio_url) playAudio(data.audio_url);
    } catch {
      setMessages((prev) => prev.map((m) => (m.id === tempId ? { ...m, text: "🎤 Audio Failed" } : m)));
      toast.error("Voice parsing failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    e.target.value = null;

    setIsLoading(true);
    const tempId = Date.now();
    setMessages((prev) => [...prev, { id: tempId, role: "user", text: `📎 Uploading ${file.name}...` }]);

    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
      const data = await response.json();

      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, text: `📎 Uploaded ${file.name}` } : m))
      );
      
      setMessages((prev) => [
        ...prev,
        { id: Date.now(), role: "ai", text: data.response, intent: data.intent },
      ]);
      if (data.audio_url) playAudio(data.audio_url);
    } catch {
      setMessages((prev) => prev.map((m) => (m.id === tempId ? { ...m, text: `📎 Upload Failed: ${file.name}` } : m)));
      toast.error("Failed to process document.");
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    { id: 1, icon: <Calendar size={18} />, label: "Schedule Meeting", color: "text-[#14e0cc]", hoverBg: "hover:bg-[#14e0cc]/10", borderHover: "hover:border-[#14e0cc]/50" },
    { id: 2, icon: <CheckSquare size={18} />, label: "Add Task", color: "text-green-400", hoverBg: "hover:bg-green-400/10", borderHover: "hover:border-green-400/50" },
    { id: 3, icon: <Folder size={18} />, label: "Save Note", color: "text-amber-400", hoverBg: "hover:bg-amber-400/10", borderHover: "hover:border-amber-400/50" },
    { id: 4, icon: <ListTodo size={18} />, label: "List Tasks", color: "text-[#7740f9]", hoverBg: "hover:bg-[#7740f9]/10", borderHover: "hover:border-[#7740f9]/50" }
  ];

  return (
    <div className="min-h-screen bg-[#0e1117] text-white flex items-center justify-center relative overflow-hidden font-sans bg-noise">
      
      {/* Background Animated Orbs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[20%] left-[30%] w-96 h-96 bg-[#7740f9] opacity-10 rounded-full blur-3xl animate-blob-1 mix-blend-screen pointer-events-none" />
        <div className="absolute bottom-[20%] right-[30%] w-[30rem] h-[30rem] bg-[#14e0cc] opacity-10 rounded-full blur-3xl animate-blob-2 mix-blend-screen pointer-events-none" />
        <div className="absolute -top-[10%] -right-[10%] w-[40rem] h-[40rem] bg-indigo-600 opacity-5 rounded-full blur-3xl mix-blend-screen" />
      </div>

      <Toaster 
        position="top-right" 
        toastOptions={{
          style: {
            background: "#141922",
            color: "#fff",
            border: "1px solid #1e2430",
            boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)",
          },
        }}
      />

      {/* Main Glass Panel */}
      <motion.div 
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={springTransition}
        className="w-full max-w-[640px] h-[100dvh] sm:h-[90vh] flex flex-col bg-[#141922]/80 backdrop-blur-xl border border-[#1e2430] sm:rounded-[24px] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.5)] relative overflow-hidden mx-0 sm:mx-4 z-10"
      >
        {/* Subtle noise inside card too */}
        <div className="absolute inset-0 bg-noise opacity-30 pointer-events-none mix-blend-overlay"></div>

        {/* Header */}
        <div className="px-6 py-5 border-b border-[#1e2430] flex justify-center items-center relative z-10 bg-gradient-to-b from-white/[0.02] to-transparent">
          <h1 className="text-[1.1rem] font-semibold bg-gradient-to-r from-[#14e0cc] to-[#7740f9] bg-clip-text text-transparent tracking-tight">
            AI Productivity Assistant
          </h1>
        </div>

        {/* Dynamic Content Area */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5 relative scrollbar-hide z-10">
          
          {/* Empty State / Quick Actions */}
          {messages.length === 0 && !isLoading && (
            <motion.div 
              initial="hidden"
              animate="visible"
              variants={{
                visible: { transition: { staggerChildren: 0.1 } }
              }}
              className="flex flex-col items-center justify-center min-h-full py-8 text-center"
            >
              <motion.div 
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 }
                }}
                transition={springTransition}
                className="relative mb-8"
              >
                {/* AI Avatar Icon */}
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#7740f9] to-indigo-900 flex items-center justify-center animate-glow relative shadow-[0_0_15px_rgba(119,64,249,0.3)]">
                  <Sparkles size={28} className="text-amber-400" />
                  
                  {/* Orbiting Teal Particle */}
                  <div className="absolute w-full h-full rounded-2xl animate-orbit pointer-events-none">
                    <div className="w-2.5 h-2.5 bg-[#14e0cc] rounded-full absolute -top-1 left-1/2 transform -translate-x-1/2 shadow-[0_0_8px_2px_rgba(20,224,204,0.8)]" />
                  </div>
                </div>
                {/* Floating animation wrapper */}
                <motion.div 
                  animate={{ y: [0, -8, 0] }} 
                  transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }} 
                  className="absolute inset-0 z-10 pointer-events-none"
                />
              </motion.div>

              <motion.div 
                 variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}
                 className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-[500px]"
              >
                {quickActions.map((action) => (
                  <motion.button 
                    key={action.id}
                    variants={{
                      hidden: { opacity: 0, scale: 0.95, y: 10 },
                      visible: { opacity: 1, scale: 1, y: 0 }
                    }}
                    transition={springTransition}
                    onClick={() => handleSendAction(action.label)}
                    className={`group relative flex items-center gap-3 p-4 bg-[#1e2430]/40 border border-[#1e2430] ${action.borderHover} rounded-xl transition-all duration-300 ease-out overflow-hidden text-left`}
                  >
                    <div className={`absolute inset-0 ${action.hoverBg} opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none`} />
                    <div className={`p-2 rounded-lg bg-[#0e1117] border border-[#1e2430] ${action.color} group-hover:scale-110 transition-transform duration-300`}>
                      {action.icon}
                    </div>
                    <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors flex-1 z-10">
                      {action.label}
                    </span>
                    <ChevronRight size={16} className={`text-gray-500 opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 ${action.color} z-10`} />
                  </motion.button>
                ))}
              </motion.div>
            </motion.div>
          )}

          {/* Chat Messages */}
          <AnimatePresence mode="popLayout">
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                layout
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                transition={springTransition}
                className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`px-5 py-3.5 rounded-[20px] max-w-[85%] sm:max-w-[75%] leading-[1.6] whitespace-pre-wrap text-[0.95rem] ${
                    msg.role === "user"
                      ? "bg-[#1e2430] border border-[#1e2430] text-gray-100 rounded-br-[4px]"
                      : "bg-[#7740f9]/10 border border-[#7740f9]/20 text-gray-200 rounded-bl-[4px]"
                  }`}
                >
                  {msg.text}
                  {msg.intent && msg.intent !== "unknown" && msg.intent !== "error" && (
                    <div className="mt-2 text-[0.65rem] tracking-wider uppercase font-medium text-[#14e0cc] bg-[#14e0cc]/10 border border-[#14e0cc]/20 px-2 py-1 rounded-md w-fit">
                      {msg.intent}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Thinking Indicator */}
          {isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} 
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start w-full"
            >
              <div className="px-5 py-4 rounded-[20px] bg-[#7740f9]/10 border border-[#7740f9]/20 rounded-bl-[4px] flex items-center gap-1.5 shadow-sm">
                <motion.div animate={{ y: [0, -5, 0], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0 }} className="w-1.5 h-1.5 bg-[#7740f9] rounded-full" />
                <motion.div animate={{ y: [0, -5, 0], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.15 }} className="w-1.5 h-1.5 bg-[#7740f9] rounded-full" />
                <motion.div animate={{ y: [0, -5, 0], opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.3 }} className="w-1.5 h-1.5 bg-[#7740f9] rounded-full" />
              </div>
            </motion.div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Bottom Input Area */}
        <div className="p-4 sm:p-5 pt-2 relative z-20">
          <div className="flex items-end gap-2 p-1.5 w-full bg-[#0e1117]/80 backdrop-blur-md border border-[#1e2430] focus-within:border-[#14e0cc]/50 focus-within:shadow-[0_0_15px_rgba(20,224,204,0.15)] transition-all duration-300 rounded-[28px]">
            
            {/* Mic Button */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
              className={`p-3 rounded-full transition-all duration-300 flex-shrink-0 ${
                isRecording 
                  ? "bg-red-500/20 text-red-400 animate-pulse" 
                  : "bg-transparent text-gray-500 hover:text-gray-300 hover:bg-[#1e2430]"
              } disabled:opacity-50`}
            >
              {isRecording ? <Square size={18} fill="currentColor" /> : <Mic size={18} />}
            </button>

            {/* Paperclip Button */}
            <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*,application/pdf" />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || isRecording}
              className="p-3 rounded-full text-gray-500 hover:text-gray-300 hover:bg-[#1e2430] transition-colors flex-shrink-0 mb-[1px] disabled:opacity-50">
               <Paperclip size={18} />
            </button>

            {/* Input Field */}
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                 if(e.key === "Enter" && !e.shiftKey) { 
                    e.preventDefault(); 
                    if(input.trim()) handleSendAction(input);
                 }
              }}
              style={{ minHeight: '44px', maxHeight: '120px' }}
              disabled={isLoading || isRecording}
              placeholder="Ask anything..."
              className="flex-1 bg-transparent border-none outline-none text-gray-200 placeholder-gray-500 px-1 py-3 text-[0.95rem] resize-none disabled:opacity-50 font-medium leading-relaxed self-center"
            />

            {/* Send Button */}
            <button
              onClick={() => handleSendAction(input)}
              disabled={!input.trim() || isLoading || isRecording}
              className={`p-3 rounded-full transition-all duration-300 flex-shrink-0 mb-[1px] ${
                input.trim() && !isLoading && !isRecording
                  ? "bg-[#14e0cc] text-[#0e1117] shadow-[0_0_15px_rgba(20,224,204,0.4)] hover:scale-105"
                  : "bg-[#1e2430] text-gray-600"
              }`}
            >
              <Send size={18} className={input.trim() ? "translate-x-0.5 -translate-y-0.5 transition-transform" : ""} />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
