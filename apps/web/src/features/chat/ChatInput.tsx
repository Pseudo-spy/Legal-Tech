"use client";

import { useState, KeyboardEvent } from "react";
import { SendHorizontal } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
}

export function ChatInput({ onSend, isStreaming }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim() && !isStreaming) {
      onSend(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 border-t bg-card">
      {isStreaming && (
        <div className="mb-2 text-xs text-muted-foreground animate-pulse">
          AI is typing...
        </div>
      )}
      <div className="relative flex items-end overflow-hidden rounded-xl border bg-background focus-within:ring-1 focus-within:ring-primary">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          placeholder="Ask a question about your contract..."
          className="min-h-[60px] w-full resize-none bg-transparent px-4 py-4 text-sm focus:outline-none disabled:opacity-50"
          rows={1}
          style={{ height: "auto" }} 
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isStreaming}
          className="m-2 shrink-0 rounded-lg bg-primary p-2 text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          aria-label="Send message"
        >
          <SendHorizontal className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
