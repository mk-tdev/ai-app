'use client';

import { useRef, useEffect } from 'react';
import { Message } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="messages-container">
        <div className="empty-state">
          <div className="empty-state-icon">💬</div>
          <h2 className="empty-state-title">Start a Conversation</h2>
          <p className="empty-state-description">
            Ask me anything! I&apos;m powered by a local LLM and ready to help.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="messages-container" ref={containerRef}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
}
