import { useState } from "react";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!input) return;

    const newMessages = [...messages, { role: "user", text: input }];
    setMessages(newMessages);
    setInput("");

    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question: input })
    });

    const data = await res.json();

    setMessages([
      ...newMessages,
      { role: "bot", text: data.answer }
    ]);
  };

  return (
    <div className="app">
      <div className="chat-box">
        <h2>Chat with Chaitran AI</h2>

        <div className="messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={msg.role === "user" ? "user-msg" : "bot-msg"}
            >
              {msg.text}
            </div>
          ))}
        </div>

        <div className="input-box">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;

