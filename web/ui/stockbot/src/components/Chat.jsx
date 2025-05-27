import { useState, useEffect, useRef } from 'react';
import '../styles/Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);

  // auto-scroll on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    setMessages(prev => [...prev, { from: 'user', text }]);
    setInput('');

    try {
      const res = await fetch('http://localhost:2811/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { from: 'bot', text: data.answer }]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { from: 'bot', text: 'Error: ' + err.message },
      ]);
    }
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-header">Chat</h2>

      <div className="chat-window" ref={scrollRef}>
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.from === 'user'
                ? 'chat-message chat-message-user'
                : 'chat-message chat-message-bot'
            }
          >
            <div className="chat-bubble">{m.text}</div>
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <textarea
          className="chat-textarea"
          rows={2}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question..."
        />
        <button className="chat-send-button" onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  );
}