'use client';

import { Message } from '@/hooks/useChat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`message ${message.role}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        {message.content ? (
          <ReactMarkdown
            className="markdown-content"
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }: any) {
                return inline ? (
                  <code className="inline-code" {...props}>{children}</code>
                ) : (
                  <pre className="code-block">
                    <code className={className} {...props}>{children}</code>
                  </pre>
                );
              },
              p({ children }) {
                return <p style={{ margin: '8px 0' }}>{children}</p>;
              },
              ul({ children }) {
                return <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '8px' }}>{children}</ul>;
              },
              ol({ children }) {
                return <ol style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '8px' }}>{children}</ol>;
              },
              li({ children }) {
                return <li style={{ marginBottom: '4px' }}>{children}</li>;
              },
              h1({ children }) {
                return <h1 style={{ fontSize: '1.5em', fontWeight: '700', margin: '16px 0 8px' }}>{children}</h1>;
              },
              h2({ children }) {
                return <h2 style={{ fontSize: '1.3em', fontWeight: '600', margin: '14px 0 6px' }}>{children}</h2>;
              },
              h3({ children }) {
                return <h3 style={{ fontSize: '1.1em', fontWeight: '600', margin: '12px 0 4px' }}>{children}</h3>;
              },
              table({ children }) {
                return <table className="markdown-table">{children}</table>;
              },
              thead({ children }) {
                return <thead className="markdown-thead">{children}</thead>;
              },
              tbody({ children }) {
                return <tbody className="markdown-tbody">{children}</tbody>;
              },
              tr({ children }) {
                return <tr className="markdown-tr">{children}</tr>;
              },
              th({ children }) {
                return <th className="markdown-th">{children}</th>;
              },
              td({ children }) {
                return <td className="markdown-td">{children}</td>;
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        ) : (
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        )}
      </div>
    </div>
  );
}
