'use client';

import { useState, useRef, KeyboardEvent, ChangeEvent } from 'react';
import { FileUploadButton } from './FileUploadButton';

interface AttachedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  message?: string;
}

interface ChatInputProps {
  onSend: (message: string, useRag: boolean) => void;
  onFileUpload: (file: File) => Promise<{ status: string; message: string }>;
  isLoading: boolean;
}

export function ChatInput({ onSend, onFileUpload, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [useRag, setUseRag] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (message.trim() && !isLoading) {
      onSend(message.trim(), useRag);
      setMessage('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  const handleFileSelect = async (files: File[]) => {
    // Add files to attached list with pending status
    const newFiles: AttachedFile[] = files.map(file => ({
      file,
      status: 'pending' as const,
    }));
    
    setAttachedFiles(prev => [...prev, ...newFiles]);
    setIsUploading(true);

    // Upload files one by one
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Update status to uploading
      setAttachedFiles(prev => 
        prev.map(f => 
          f.file === file ? { ...f, status: 'uploading' as const } : f
        )
      );

      try {
        const result = await onFileUpload(file);
        
        // Update status based on result
        setAttachedFiles(prev => 
          prev.map(f => 
            f.file === file 
              ? { 
                  ...f, 
                  status: result.status === 'error' ? 'error' : 'success',
                  message: result.message 
                } 
              : f
          )
        );
      } catch (error) {
        setAttachedFiles(prev => 
          prev.map(f => 
            f.file === file 
              ? { ...f, status: 'error', message: 'Upload failed' } 
              : f
          )
        );
      }
    }

    setIsUploading(false);
    
    // Clear successful uploads after 3 seconds
    setTimeout(() => {
      setAttachedFiles(prev => prev.filter(f => f.status !== 'success'));
    }, 3000);
  };

  const removeFile = (file: File) => {
    setAttachedFiles(prev => prev.filter(f => f.file !== file));
  };

  return (
    <div className="input-container">
      {/* Attached files display */}
      {attachedFiles.length > 0 && (
        <div className="attached-files">
          {attachedFiles.map((af, index) => (
            <div 
              key={`${af.file.name}-${index}`} 
              className={`attached-file-chip ${af.status}`}
            >
              <span className="file-icon">📄</span>
              <span className="file-name">{af.file.name}</span>
              {af.status === 'uploading' && (
                <span className="file-status uploading">⏳</span>
              )}
              {af.status === 'success' && (
                <span className="file-status success">✓</span>
              )}
              {af.status === 'error' && (
                <span className="file-status error" title={af.message}>✗</span>
              )}
              {(af.status === 'pending' || af.status === 'error') && (
                <button 
                  className="file-remove"
                  onClick={() => removeFile(af.file)}
                  aria-label="Remove file"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="input-wrapper">
        <FileUploadButton 
          onFileSelect={handleFileSelect}
          isUploading={isUploading}
        />
        <textarea
          ref={textareaRef}
          className="input-field"
          placeholder="Type your message..."
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
        />
        <button 
          className="send-button"
          onClick={handleSubmit}
          disabled={!message.trim() || isLoading}
          aria-label="Send message"
        >
          <svg 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
      <label className="rag-toggle">
        <input
          type="checkbox"
          checked={useRag}
          onChange={(e) => setUseRag(e.target.checked)}
        />
        <span>Use RAG (search knowledge base)</span>
      </label>
    </div>
  );
}
