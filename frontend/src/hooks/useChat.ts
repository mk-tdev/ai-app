'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface UploadResult {
  status: string;
  message: string;
  filename?: string;
  chunks_created?: number;
}

interface UseChatOptions {
  apiUrl?: string;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string, useRag?: boolean, useReasoning?: boolean, maxHops?: number) => Promise<void>;
  uploadDocument: (file: File) => Promise<UploadResult>;
  clearMessages: () => void;
  sessionId: string | null;
  newConversation: () => void;
}

const SESSION_STORAGE_KEY = 'ai_chat_session_id';

// Generate a UUID v4
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const { apiUrl = 'http://localhost:8000' } = options;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initialize session ID from localStorage on mount, or create new one
  useEffect(() => {
    const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      // Create new session ID automatically on first load
      const newSessionId = generateUUID();
      setSessionId(newSessionId);
      localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    }
  }, []);

  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const uploadDocument = useCallback(async (file: File): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed: ${response.status}`);
      }

      const result = await response.json();
      return {
        status: result.status,
        message: result.message,
        filename: result.filename,
        chunks_created: result.chunks_created,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      return {
        status: 'error',
        message,
      };
    }
  }, [apiUrl]);

  const sendMessage = useCallback(async (
    content: string,
    useRag: boolean = false,
    useReasoning: boolean = false,
    maxHops: number = 3
  ) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    // Generate or use existing session ID
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = generateUUID();
      setSessionId(currentSessionId);
      localStorage.setItem(SESSION_STORAGE_KEY, currentSessionId);
    }

    // Add user message
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Create placeholder for assistant message
    const assistantId = generateId();
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMessage]);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content.trim(),
          conversation_id: currentSessionId,
          use_rag: useRag,
          use_reasoning: useReasoning,
          max_hops: maxHops,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE events
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          // SSE format uses "event:" and "data:" lines
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const data = line.slice(5).trim();
            if (data) {
              try {
                const parsed = JSON.parse(data);
                
                // Handle token events
                if (currentEvent === 'token' && parsed.token) {
                  // Use flushSync to force immediate update and prevent batching
                  flushSync(() => {
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === assistantId 
                          ? { ...msg, content: msg.content + parsed.token }
                          : msg
                      )
                    );
                  });
                }
                
                // Handle error events
                if (currentEvent === 'error' && parsed.error) {
                  setError(parsed.error);
                }
              } catch {
                // Ignore parse errors for malformed events
              }
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          // Request was cancelled
          return;
        }
        setError(err.message);
        
        // Update assistant message with error
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantId
              ? { ...msg, content: 'Sorry, I encountered an error. Please try again.' }
              : msg
          )
        );
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [apiUrl, isLoading, sessionId]);

  const clearMessages = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
    setError(null);
  }, []);

  const newConversation = useCallback(() => {
    // Clear current session and create new one
    const newSessionId = generateUUID();
    setSessionId(newSessionId);
    localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    setMessages([]);
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    uploadDocument,
    clearMessages,
    sessionId,
    newConversation,
  };
}

