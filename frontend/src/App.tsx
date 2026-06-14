import { useState, useRef, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Document {
  id: string;
  filename: string;
  status: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadMessageType, setUploadMessageType] = useState<'success' | 'error' | ''>('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'simple' | 'deep' | 'exact'>('simple');
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const savedDocs = localStorage.getItem('rag_documents');
    if (savedDocs) {
      try {
        setDocuments(JSON.parse(savedDocs));
      } catch (e) {
        console.error('Failed to load saved documents');
      }
    }
  }, []);

  const saveDocuments = (docs: Document[]) => {
    setDocuments(docs);
    localStorage.setItem('rag_documents', JSON.stringify(docs));
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadMessage('Please select a file');
      setUploadMessageType('error');
      return;
    }

    setUploading(true);
    setUploadMessage('');
    setUploadMessageType('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        const newDoc: Document = {
          id: data.document_id,
          filename: file.name,
          status: 'ready'
        };
        const updatedDocs = [...documents, newDoc];
        saveDocuments(updatedDocs);
        setSelectedDocIds([data.document_id]);
        setCurrentConversationId(null);
        setMessages([]);
        setUploadMessage(`Uploaded: ${file.name} (${data.chunk_count} chunks ready)`);
        setUploadMessageType('success');
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        setUploadMessage(`Upload failed: ${data.detail || 'Unknown error'}`);
        setUploadMessageType('error');
      }
    } catch (error) {
      setUploadMessage('Upload failed. Make sure the backend is running');
      setUploadMessageType('error');
    } finally {
      setUploading(false);
    }
  };

  const toggleDocument = (docId: string) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    if (selectedDocIds.length === 0) {
      setUploadMessage('Please upload or select a document first');
      setUploadMessageType('error');
      setTimeout(() => setUploadMessageType(''), 3000);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    const assistantMessageId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_ids: selectedDocIds,
          question: userMessage.content,
          mode: mode,
          conversation_id: currentConversationId,
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        if (data.conversation_id) {
          setCurrentConversationId(data.conversation_id);
        }
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: data.answer }
            : msg
        ));
      } else {
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: `Error: ${data.detail || 'Something went wrong'}` }
            : msg
        ));
      }
    } catch (error) {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: 'Error: Failed to connect to backend' }
          : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
  };

  const handleDeleteDocument = (docId: string) => {
    const updatedDocs = documents.filter(d => d.id !== docId);
    saveDocuments(updatedDocs);
    if (selectedDocIds.includes(docId)) {
      setSelectedDocIds(selectedDocIds.filter(id => id !== docId));
      setCurrentConversationId(null);
      setMessages([]);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="text-center mb-10 pt-8">
          <div className="inline-flex items-center justify-center mb-5">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-4 shadow-lg">
              <span className="text-5xl">📚</span>
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent mb-3">
            RAG Document QA System
          </h1>
          <p className="text-lg text-gray-500 max-w-lg mx-auto">
            Upload documents and ask questions using AI-powered retrieval
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span className="text-2xl">📄</span>
                Upload Document
              </h2>
              
              <div className="mb-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors cursor-pointer"
                     onClick={() => fileInputRef.current?.click()}>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                  {file ? (
                    <div>
                      <div className="text-3xl mb-2">📎</div>
                      <p className="text-base text-gray-700 font-medium">{file.name}</p>
                      <p className="text-sm text-gray-400 mt-1">{(file.size / 1024).toFixed(2)} KB</p>
                    </div>
                  ) : (
                    <div>
                      <div className="text-4xl mb-2">📂</div>
                      <p className="text-base text-gray-500">Click or drag to upload</p>
                      <p className="text-sm text-gray-400 mt-1">PDF, DOCX, TXT (max 10MB)</p>
                    </div>
                  )}
                </div>
              </div>

              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium py-3 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg text-base"
              >
                {uploading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Uploading...
                  </span>
                ) : 'Upload Document'}
              </button>

              {uploadMessage && (
                <div className={`mt-4 p-3 rounded-xl text-sm ${
                  uploadMessageType === 'success' 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : uploadMessageType === 'error'
                    ? 'bg-red-50 text-red-700 border border-red-200'
                    : 'bg-gray-50 text-gray-600'
                }`}>
                  {uploadMessage}
                </div>
              )}
            </div>

            {documents.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <span className="text-2xl">📑</span>
                  Your Documents
                  <span className="text-sm text-gray-400 ml-auto">{documents.length} total</span>
                </h2>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {documents.map(doc => (
                    <div
                      key={doc.id}
                      className={`group p-3 rounded-xl cursor-pointer transition-all ${
                        selectedDocIds.includes(doc.id)
                          ? 'bg-blue-50 border border-blue-200 shadow-sm'
                          : 'bg-gray-50 hover:bg-gray-100 border border-transparent'
                      }`}
                      onClick={() => toggleDocument(doc.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <input
                            type="checkbox"
                            checked={selectedDocIds.includes(doc.id)}
                            onChange={() => toggleDocument(doc.id)}
                            onClick={(e) => e.stopPropagation()}
                            className="w-4 h-4 text-blue-600 rounded"
                          />
                          <span className="text-xl">📄</span>
                          <span className="text-base font-medium text-gray-700 truncate">{doc.filename}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {doc.status === 'ready' && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Ready</span>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteDocument(doc.id);
                            }}
                            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            <div className="chat-container flex flex-col h-[700px]">
              <div className="bg-gradient-to-r from-gray-50 to-white border-b px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                      <span className="text-2xl">💬</span>
                      Ask Questions
                    </h2>
                    {selectedDocIds.length > 0 ? (
                      <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                        <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                        {selectedDocIds.length} document(s) selected
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400 mt-1">Select documents to start asking</p>
                    )}
                  </div>
                  {messages.length > 0 && (
                    <button
                      onClick={handleClearChat}
                      className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      Clear chat
                    </button>
                  )}
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center py-20">
                    <div className="text-7xl mb-4">🤖</div>
                    <p className="text-gray-500 text-lg mb-2">Ask me anything about your documents</p>
                    <p className="text-base text-gray-400">
                      Try: "What is this document about?"
                    </p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[80%] ${msg.role === 'user' ? 'message-user' : 'message-assistant'}`}>
                        <div className="px-5 py-3">
                          <p className="whitespace-pre-wrap text-base leading-relaxed">
                            {msg.content || (
                              <span className="flex items-center gap-2">
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Thinking...
                              </span>
                            )}
                          </p>
                          <p className={`text-xs mt-2 ${
                            msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'
                          }`}>
                            {msg.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {loading && messages[messages.length - 1]?.content !== '' && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-2xl rounded-bl-md px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2.5 h-2.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2.5 h-2.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="border-t p-5 bg-gray-50">
                <div className="flex gap-3">
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value as 'simple' | 'deep' | 'exact')}
                    className="px-3 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white cursor-pointer"
                  >
                    <option value="simple">⚡ Simple</option>
                    <option value="deep">🔍 Deep Thinking</option>
                    <option value="exact">📄 Exact</option>
                  </select>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !loading && selectedDocIds.length > 0 && handleSend()}
                    placeholder={selectedDocIds.length > 0 ? "Ask a question..." : "Select documents first"}
                    disabled={selectedDocIds.length === 0 || loading}
                    className="flex-1 px-5 py-3 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-400 transition-all"
                  />
                  <button
                    onClick={handleSend}
                    disabled={selectedDocIds.length === 0 || loading || !input.trim()}
                    className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg text-base"
                  >
                    {loading ? 'Sending...' : 'Send'}
                  </button>
                </div>
                <p className="text-sm text-gray-400 text-center mt-3">
                  Powered by RAG + {selectedDocIds.length > 0 ? 'LLM ready' : 'Select documents'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mt-10 pb-6">
          <p className="text-sm text-gray-400">
            Built with FastAPI + LangChain + React + TypeScript + TailwindCSS
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;