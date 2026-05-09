"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage as IChatMessage } from "@/types/api";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { useApiClient } from "@/lib/api";

interface ChatWindowProps {
  contractId: string;
  jobId: string;
}

const STARTER_QUESTIONS = [
  "Can I work for a competitor after I leave?",
  "Who owns the code I write on weekends?",
  "What happens if I'm terminated?",
  "Are there any unusual intellectual property clauses?",
];

export function ChatWindow({ contractId, jobId }: ChatWindowProps) {
  const [messages, setMessages] = useState<IChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { chat } = useApiClient();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    const newUserMsg: IChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      clause_citation: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setIsStreaming(true);

    try {
      const response = await chat(contractId, text);
      setMessages((prev) => [...prev, response]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "Sorry, I encountered an error while processing your request.",
          clause_citation: null,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-full flex-col bg-muted/20">
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center space-y-8 p-4">
            <div className="text-center space-y-2">
              <h3 className="text-xl font-bold tracking-tight">Contract Q&A</h3>
              <p className="text-sm text-muted-foreground">
                Ask specific questions about your contract, and our legal AI will answer based on the analysis.
              </p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
              {STARTER_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="rounded-lg border bg-card p-4 text-sm font-medium text-left transition-colors hover:bg-muted"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4 pb-4">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} jobId={jobId} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={handleSend} isStreaming={isStreaming} />
      </div>
    </div>
  );
}
