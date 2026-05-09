import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";
import { ChatMessage as IChatMessage } from "@/types/api";
import { ClauseCitation } from "./ClauseCitation";

interface ChatMessageProps {
  message: IChatMessage;
  jobId: string;
}

export function ChatMessage({ message, jobId }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex w-full gap-4 p-4", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <Bot className="h-5 w-5 text-primary" />
        </div>
      )}
      
      <div className={cn("flex max-w-[80%] flex-col gap-2")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-muted/50 text-foreground rounded-tl-sm border"
          )}
        >
          {message.content}
        </div>
        
        {message.clause_citation && !isUser && (
          <ClauseCitation clauseId={message.clause_citation} jobId={jobId} label="View referenced clause" />
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
          <User className="h-5 w-5 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}
