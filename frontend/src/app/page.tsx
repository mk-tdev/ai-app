'use client';

import { useChat } from '@/hooks/useChat';
import { MessageList, ChatInput } from '@/components';

export default function Home() {
  const { messages, isLoading, error, sendMessage, uploadDocument, newConversation, sessionId } = useChat({
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  });

  return (
    <div className="app-container">
      <header className="header">
        <div>
          <h1 className="header-title">AI Chat</h1>
          <p className="header-subtitle">Powered by llama.cpp & LangGraph</p>
        </div>
      </header>

      <main className="chat-container">
        {/* Session info bar at top of chat */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 20px',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          borderBottom: '1px solid #e0e0e0',
          borderRadius: '8px 8px 0 0',
          marginBottom: '10px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ 
              fontSize: '13px', 
              fontWeight: '600', 
              color: '#333',
              letterSpacing: '0.3px'
            }}>
              Session ID:
            </span>
            {sessionId && (
              <code style={{ 
                fontSize: '12px', 
                color: '#0066cc',
                background: 'rgba(255, 255, 255, 0.7)',
                padding: '4px 10px',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontWeight: '500',
                letterSpacing: '0.5px'
              }}>
                {sessionId}
              </code>
            )}
          </div>
          
          <button
            onClick={newConversation}
            style={{
              padding: '8px 18px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.3)';
            }}
          >
            ✨ New Conversation
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <MessageList messages={messages} isLoading={isLoading} />
        
        <ChatInput 
          onSend={sendMessage} 
          onFileUpload={uploadDocument}
          isLoading={isLoading} 
        />
      </main>
    </div>
  );
}

