import { useState, useRef, useEffect } from 'react';
import { X, Send, Sparkles, Bot, User, ChevronRight, ChevronDown } from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';

interface Message {
  role: 'user' | 'ai';
  content: string;
  thinking?: string;
}

const ThinkingBlock = ({ content }: { content: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  if (!content) return null;

  return (
    <div className="mb-2 rounded-lg border border-stone-200 bg-stone-50 overflow-hidden">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full px-3 py-2 text-xs font-medium text-stone-500 hover:bg-stone-100 transition-colors"
      >
        {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        Mentor's Thinking Process
      </button>
      {isExpanded && (
        <div className="px-3 py-2 text-xs text-stone-600 border-t border-stone-200 bg-white font-mono whitespace-pre-wrap">
          {content}
        </div>
      )}
    </div>
  );
};

export const MentorChat = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: "Hello! I'm your research mentor. How can I help you refine your hypothesis today?" }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const parseResponse = (fullResponse: string): { thinking?: string, content: string } => {
    const thinkingMatch = fullResponse.match(/<thinking>([\s\S]*?)<\/thinking>/);
    if (thinkingMatch) {
      const thinking = thinkingMatch[1].trim();
      const content = fullResponse.replace(/<thinking>[\s\S]*?<\/thinking>/, '').trim();
      return { thinking, content };
    }
    return { content: fullResponse };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userMsg }),
      });
      
      if (!res.ok) throw new Error('Failed to fetch');
      
      const json = await res.json();
      const { thinking, content } = parseResponse(json.response);
      
      setMessages(prev => [...prev, { role: 'ai', content, thinking }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: "Sorry, I encountered an error connecting to the backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute right-4 top-16 bottom-4 w-[400px] bg-white rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-stone-200 flex flex-col z-50 overflow-hidden animate-in slide-in-from-right-10 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-stone-100 bg-stone-50/80 backdrop-blur-sm">
        <div className="flex items-center gap-2 font-medium text-stone-700">
          <Sparkles size={16} className="text-yellow-500" />
          Research Mentor
        </div>
        <button onClick={onClose} className="text-stone-400 hover:text-stone-600 transition-colors">
          <X size={18} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-stone-50/30" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm
              ${msg.role === 'ai' ? 'bg-white text-indigo-500 border border-stone-100' : 'bg-stone-800 text-white'}
            `}>
              {msg.role === 'ai' ? <Bot size={16} /> : <User size={16} />}
            </div>
            <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {msg.role === 'ai' && msg.thinking && <ThinkingBlock content={msg.thinking} />}
                <div className={`
                  rounded-2xl px-4 py-3 text-sm shadow-sm
                  ${msg.role === 'ai' ? 'bg-white border border-stone-100 text-stone-700' : 'bg-stone-800 text-white'}
                `}>
                  {msg.role === 'ai' ? (
                    <MarkdownRenderer content={msg.content} />
                  ) : (
                    msg.content
                  )}
                </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
             <div className="w-8 h-8 rounded-full bg-white border border-stone-100 flex items-center justify-center shadow-sm">
                <Bot size={16} className="text-indigo-500 animate-pulse" />
             </div>
             <div className="bg-white border border-stone-100 px-4 py-3 rounded-2xl text-sm text-stone-400 shadow-sm">
                Thinking...
             </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-stone-100">
        <form onSubmit={handleSubmit} className="relative">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask follow-up questions..."
            className="w-full bg-stone-50 border border-stone-200 rounded-xl py-3 pl-4 pr-12 text-sm outline-none focus:ring-2 focus:ring-stone-200 transition-all placeholder-stone-400 focus:bg-white"
          />
          <button 
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 top-2 p-1.5 bg-stone-800 text-white rounded-lg hover:bg-stone-700 disabled:opacity-50 disabled:hover:bg-stone-800 transition-colors shadow-sm"
          >
            <Send size={14} />
          </button>
        </form>
      </div>
    </div>
  );
};
