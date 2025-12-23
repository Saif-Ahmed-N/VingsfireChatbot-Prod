import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageSquare, X, Send, Paperclip, ChevronLeft, Minimize2, CheckCircle2, ChevronDown, ArrowRight, Sparkles, Zap, Globe, Shield, MessageCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- CONFIGURATION ---
const API_URL = "https://vingsfirechatbot-prod.onrender.com";
const LOGO_PATH = "/logo.png"; 

// --- WELCOME FEATURES ---
const FEATURES = [
  { icon: MessageCircle, title: 'Chat smarter', desc: 'AI-powered responses', color: 'from-purple-500 to-pink-500' },
  { icon: Zap, title: 'Instant Support', desc: '24/7 availability', color: 'from-cyan-500 to-blue-500' },
  { icon: Globe, title: 'Global Reach', desc: 'Multi-language support', color: 'from-emerald-500 to-teal-500' },
  { icon: Shield, title: 'Secure', desc: 'Enterprise security', color: 'from-orange-500 to-red-500' },
];

// --- COMPONENT: CHAT HEADER (Liquid Style) ---
const ChatHeader = ({ onClose }) => (
  <div 
    className="px-6 py-5 flex items-center justify-between relative overflow-hidden shrink-0 z-20"
    style={{
      background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.15) 50%, rgba(236, 72, 153, 0.15) 100%)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    }}
  >
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer pointer-events-none" />
    
    <div className="flex items-center gap-3 relative z-10">
      <div 
        className="w-12 h-12 rounded-2xl flex items-center justify-center p-2 shadow-lg relative overflow-hidden"
        style={{
          background: 'rgba(255, 255, 255, 0.2)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
        }}
      >
        <img src={LOGO_PATH} alt="Infinite Tech" className="w-full h-full object-cover" />
      </div>
      <div>
        <h3 className="text-white font-display tracking-wide font-bold drop-shadow-md">Infinite Tech</h3>
        <div className="flex items-center gap-2 mt-0.5">
          <motion.div
            animate={{ scale: [1, 1.2, 1], opacity: [1, 0.8, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-2 h-2 rounded-full"
            style={{
              background: 'linear-gradient(135deg, #10b981, #34d399)',
              boxShadow: '0 0 10px rgba(16, 185, 129, 0.8)',
            }}
          />
          <span className="text-white/80 text-xs font-display tracking-wider">AI AGENT ONLINE</span>
        </div>
      </div>
    </div>
    
    <motion.button
      whileHover={{ scale: 1.1, rotate: 90 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClose}
      className="relative z-10 p-2 text-white/80 hover:text-white rounded-xl transition-all"
      style={{ background: 'rgba(255, 255, 255, 0.1)' }}
    >
      <X className="w-5 h-5" />
    </motion.button>
  </div>
);

// --- COMPONENT: WELCOME SCREEN ---
const WelcomeScreen = () => (
  <motion.div 
    key="welcome"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="flex-1 flex flex-col items-center justify-center p-6 space-y-6 relative z-10"
  >
    <motion.div 
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.2 }}
      className="relative"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-400 via-purple-400 to-pink-400 rounded-full blur-2xl opacity-50 animate-pulse" />
      <img src={LOGO_PATH} alt="Logo" className="w-24 h-24 relative z-10 animate-float" />
    </motion.div>

    <motion.div 
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.4 }}
      className="text-center space-y-2"
    >
      <h2 className="font-display text-white text-2xl font-bold">Hey there! 👋</h2>
      <p className="text-white/70 text-sm">Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 font-semibold">Infinite Tech</span></p>
    </motion.div>

    <motion.div 
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.6 }}
      className="grid grid-cols-2 gap-3 w-full"
    >
      {FEATURES.map((feature, index) => (
        <div key={index} className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-colors group">
          <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-2 shadow-lg`}>
            <feature.icon size={16} className="text-white" />
          </div>
          <div className="text-white text-xs font-bold">{feature.title}</div>
          <div className="text-white/50 text-[10px]">{feature.desc}</div>
        </div>
      ))}
    </motion.div>
  </motion.div>
);

// --- MAIN WIDGET ---
export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  
  const [chatState, setChatState] = useState({ stage: 'get_name', user_details: { stage_history: [] } });
  const [uiElements, setUiElements] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, uiElements, isLoading]);

  useEffect(() => {
    if (isOpen) {
      setShowWelcome(true);
      if (!hasStarted) {
         handleSendMessage("new proposal", "command", null, true);
         setHasStarted(true);
      }
      const timer = setTimeout(() => setShowWelcome(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const handleClose = () => {
      setIsOpen(false);
      setTimeout(() => {
          setMessages([]);
          setChatState({ stage: 'get_name', user_details: { stage_history: [] } });
          setUiElements(null);
          setHasStarted(false);
      }, 300);
  };

  const handleSendMessage = async (textOverride = null, type = 'text', displayInput = null, isHiddenCommand = false) => {
    const userMessage = textOverride || input;
    if (!userMessage.trim()) return;

    if (!isHiddenCommand && userMessage !== '__GO_BACK__') {
        setMessages(prev => [...prev, { role: 'user', content: displayInput || userMessage }]);
    }
    
    setInput("");
    setUiElements(null); 
    setIsLoading(true); 

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        stage: chatState.stage,
        user_details: chatState.user_details,
        user_input: userMessage
      });
      const data = response.data;

      setTimeout(() => {
          setChatState(prev => ({ ...prev, stage: data.next_stage, user_details: data.user_details }));
          if (data.bot_message) setMessages(prev => [...prev, { role: 'assistant', content: data.bot_message }]);
          if (data.ui_elements) setUiElements(data.ui_elements);
          if (data.next_stage === 'final_generation') triggerProposalGeneration(data.user_details);
          setIsLoading(false); 
      }, 1000); 

    } catch (error) {
      console.error(error);
      setIsLoading(false);
    }
  };

  const triggerProposalGeneration = async (finalUserDetails) => {
    try {
        // 1. Trigger Backend Generation (Background)
        await axios.post(`${API_URL}/generate-proposal`, {
            user_details: finalUserDetails,
            category: finalUserDetails.category,
            custom_category_name: finalUserDetails.custom_category_name,
            custom_category_data: chatState.custom_category_data
        });

        // 2. Show Success Message & OPTIONS Automatically
        setTimeout(() => {
             setMessages(prev => [...prev, { 
                 role: 'assistant', 
                 content: "✅ **Proposal Sent!** Please check your email inbox.\n\nIs there anything else I can help you with?" 
             }]);
             
             // --- FIX: Force buttons to appear immediately ---
             setUiElements({
                 type: 'buttons',
                 options: ["Create Another Proposal", "Visit Website", "Contact Sales"]
             });

             setChatState(prev => ({ ...prev, stage: 'post_engagement' }));
        }, 2000);

    } catch (error) { 
        console.error(error);
        setMessages(prev => [...prev, { role: 'assistant', content: "⚠️ Proposal generation initiated, but server response timed out. Please check your email shortly." }]);
    }
  };

  const renderUiElements = () => {
    if (!uiElements) return null;

    switch (uiElements.type) {
      case 'buttons':
      case 'dropdown':
        return (
          <div className="flex flex-wrap justify-center gap-3 mt-4 w-full px-4 pb-2 animate-fade-in">
            {uiElements.options.map((option, idx) => (
              <motion.button
                key={idx}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleSendMessage(option, 'button')}
                // FIGMA STYLE PILL
                className="px-5 py-2 bg-white/10 backdrop-blur-md border border-white/20 text-white rounded-full hover:bg-cyan-500/20 hover:border-cyan-400 transition-all flex items-center gap-2 text-sm shadow-sm"
              >
                {option}
              </motion.button>
            ))}
          </div>
        );
      
      case 'file_upload':
        return (
          <div className="mt-4 p-6 border border-dashed border-white/20 rounded-2xl bg-white/5 text-center hover:bg-white/10 transition-colors cursor-pointer group">
             <input type="file" id="file-upload" className="hidden" onChange={(e) => handleFileUpload(e.target.files[0])}/>
             <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-3">
                <div className="p-3 bg-white/10 rounded-full group-hover:scale-110 transition-transform">
                    <Paperclip className="w-5 h-5 text-cyan-400" />
                </div>
                <span className="text-sm text-white font-medium">Upload Resume</span>
                <span className="text-xs text-white/40">PDF, DOCX</span>
             </label>
          </div>
        );

      case 'form':
         return (
             <div className="mt-4 p-5 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md">
                 <label className="block text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3">Contact Details</label>
                 <div className="flex gap-3">
                    <div className="relative w-[35%]">
                        <select id="country-select" className="w-full appearance-none p-3 bg-white/5 border border-white/10 rounded-xl text-sm font-medium text-white focus:outline-none focus:border-cyan-500 transition-colors">
                            {uiElements.options.length > 0 ? uiElements.options.map(opt => <option key={opt} value={opt} className="bg-slate-900">{opt}</option>) : <option value="India" className="bg-slate-900">India</option>}
                        </select>
                        <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-white/30 pointer-events-none" />
                    </div>
                    <input id="phone-input" type="tel" placeholder="9876543210" className="w-[65%] p-3 bg-white/5 border border-white/10 rounded-xl text-sm font-medium text-white focus:outline-none focus:border-cyan-500 placeholder:text-white/20 transition-colors" />
                 </div>
                 <button onClick={() => {
                        const c = document.getElementById('country-select').value;
                        const p = document.getElementById('phone-input').value;
                        if(p) handleSendMessage(`${c}:${p}`, 'form', `Selected ${c}`);
                    }}
                    className="w-full mt-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold py-3 rounded-xl text-sm hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] transition-all"
                 >
                    Confirm <CheckCircle2 className="w-4 h-4 inline ml-1" />
                 </button>
             </div>
         )
      default: return null;
    }
  };

  const handleFileUpload = async (file) => {
      if(!file) return;
      const formData = new FormData();
      formData.append('resume', file);
      formData.append('email', uiElements.user_email);
      setMessages(prev => [...prev, { role: 'assistant', content: `Uploading **${file.name}**...` }]);
      setIsLoading(true);
      try {
          await axios.post(`${API_URL}${uiElements.upload_to}`, formData);
          setTimeout(() => {
             handleSendMessage(`Uploaded: ${file.name}`, 'file');
             setIsLoading(false);
          }, 2000);
      } catch (e) {
          setMessages(prev => [...prev, { role: 'assistant', content: "❌ Upload failed." }]);
          setIsLoading(false);
      }
  };

  return (
    <div className="fixed bottom-10 right-10 z-50 flex flex-col items-end font-sans">
      <AnimatePresence mode="wait">
        
        {isOpen && (
          <motion.div 
            key="chat-window"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            // --- FIX: Height set to 900px, Liquid background ---
            className="fixed bottom-[50px] right-20 w-[420px] h-[900px] max-h-[calc(100vh-100px)] flex flex-col overflow-hidden rounded-[32px] border border-white/10 shadow-2xl"
            style={{
              background: '#0F172A', // Dark base
              boxShadow: '0 40px 80px -12px rgba(0, 0, 0, 0.8)',
            }}
          >
            <AnimatePresence mode="wait">
              {showWelcome ? (
                <WelcomeScreen key="welcome" />
              ) : (
                <motion.div 
                  key="chat-interface"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex-1 flex flex-col h-full"
                >
                  <ChatHeader onClose={handleClose} />

                  <div className="flex-1 p-6 overflow-y-auto space-y-6 scrollbar-thin scrollbar-thumb-white/10 relative">
                    {/* LIQUID BACKGROUND GLOWS */}
                    <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none opacity-20">
                        <div className="absolute top-[-10%] left-[-10%] w-[300px] h-[300px] bg-purple-600 rounded-full blur-[100px]" />
                        <div className="absolute bottom-[-10%] right-[-10%] w-[300px] h-[300px] bg-cyan-600 rounded-full blur-[100px]" />
                    </div>

                    {messages.map((msg, idx) => (
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        key={idx} 
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-end gap-3 relative z-10`}
                      >
                        {msg.role === 'assistant' && (
                          <div className="w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg bg-white/5 border border-white/10">
                              <img src={LOGO_PATH} className="w-6 h-6 object-contain" />
                          </div>
                        )}
                        <div className={`max-w-[85%] p-4 text-[15px] font-medium leading-relaxed shadow-lg backdrop-blur-md ${
                          msg.role === 'user' 
                            ? 'rounded-2xl rounded-br-none text-white bg-gradient-to-br from-cyan-500 to-blue-600' 
                            : 'rounded-2xl rounded-bl-none text-white/90 bg-white/5 border border-white/10'
                        }`}>
                          <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<b class="font-bold text-white">$1</b>').replace(/\n/g, '<br />') }} />
                        </div>
                      </motion.div>
                    ))}
                    
                    {/* --- FIX: LOADING STATE WITH LOGO --- */}
                    {isLoading && (
                      <div className="flex gap-3 items-end">
                         <div className="w-10 h-10 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                            <img src={LOGO_PATH} className="w-6 h-6 object-contain opacity-80" />
                         </div>
                         <div className="bg-white/5 border border-white/10 px-4 py-3 rounded-2xl rounded-bl-none flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce"></span>
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                            <span className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                         </div>
                      </div>
                    )}
                    
                    {!isLoading && renderUiElements()}
                    <div ref={messagesEndRef} />
                  </div>

                  <div className="p-5 border-t border-white/10 bg-black/20 backdrop-blur-xl relative z-20">
                     {chatState.user_details.stage_history?.length > 0 && (
                       <button onClick={() => handleSendMessage('__GO_BACK__', 'command')} className="flex items-center gap-1 text-[10px] font-bold text-white/40 hover:text-cyan-400 mb-2 transition-colors uppercase">
                         <ChevronLeft size={12} /> Back Step
                       </button>
                     )}
                     <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="flex gap-3">
                       <input
                         type="text"
                         value={input}
                         onChange={(e) => setInput(e.target.value)}
                         disabled={isLoading} 
                         placeholder="Type a message..."
                         className="flex-1 bg-white/10 border border-white/20 rounded-2xl px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 placeholder:text-white/30 transition-all"
                       />
                       <motion.button 
                         whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                         type="submit" disabled={!input.trim()}
                         className="p-3 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl text-white shadow-lg disabled:opacity-50"
                       >
                         <Send size={20} />
                       </motion.button>
                     </form>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {!isOpen && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsOpen(true)}
            // CHANGED: w-20 h-20 -> w-14 h-14 (Matches WhatsApp Size)
            // CHANGED: bottom-10 right-10 -> bottom-5 right-5 (Matches WhatsApp Position)
            className="fixed bottom-5 right-5 w-15 h-15 rounded-full shadow-[0_0_30px_rgba(6,182,212,0.6)] flex items-center justify-center z-50 overflow-hidden group"
            style={{ background: 'linear-gradient(135deg, #06b6d4 0%, #8b5cf6 50%, #ec4899 100%)' }}
          >
            <div className="absolute inset-0 animate-shimmer opacity-50" />
            {/* CHANGED: w-12 h-12 -> w-8 h-8 (Resized inner logo to fit) */}
            <img src={LOGO_PATH} alt="Chat" className="w-10 h-10 relative z-10 animate-float drop-shadow-md" />
            <div className="absolute inset-0 bg-white/20 rounded-full scale-0 group-hover:scale-100 transition-transform duration-300" />
          </motion.button>
        )}

      </AnimatePresence>
    </div>
  );
}