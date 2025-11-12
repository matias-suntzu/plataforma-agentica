'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertCircle, CheckCircle, Bot, User } from 'lucide-react';

const API_URL = 'https://plataforma-agentica.onrender.com';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  workflow_type?: string;
  metadata?: any;
  isError?: boolean;
}

interface Status {
  type: 'idle' | 'success' | 'warning' | 'error';
  message: string;
}

export default function MetaAdsAgent() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '¡Hola! Soy tu asistente de Meta Ads. ¿En qué puedo ayudarte hoy?', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Status>({ type: 'idle', message: '' });
  const [threadId] = useState(() => `thread_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      const data = await res.json();
      if (data.status === 'healthy') {
        setStatus({ type: 'success', message: 'Conectado' });
      } else {
        setStatus({ type: 'warning', message: 'API degradada' });
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'API no disponible' });
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: currentInput,
          thread_id: threadId,
          user_id: 'demo_user'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.content,
        workflow_type: data.workflow_type,
        metadata: data.metadata,
        timestamp: new Date(data.timestamp)
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStatus({ type: 'success', message: 'Respuesta recibida' });
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}. Por favor, verifica que la API esté funcionando.`,
        timestamp: new Date(),
        isError: true
      }]);
      setStatus({ type: 'error', message: 'Error al enviar mensaje' });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    "¿Qué campañas tengo activas?",
    "Muéstrame el rendimiento de mis anuncios",
    "¿Cuál es mi presupuesto actual?",
    "Ayúdame a crear una nueva campaña"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 p-3 rounded-full">
                <Bot size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Meta Ads Agent</h1>
                <p className="text-sm text-blue-100">Asistente inteligente para Meta Advertising</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2 bg-white/10 px-3 py-1 rounded-full">
              {status.type === 'success' && <CheckCircle size={16} className="text-green-300" />}
              {status.type === 'error' && <AlertCircle size={16} className="text-red-300" />}
              {status.type === 'warning' && <AlertCircle size={16} className="text-yellow-300" />}
              <span className="text-sm">{status.message || 'Verificando...'}</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
                  : 'bg-gradient-to-br from-blue-500 to-cyan-500'
              }`}>
                {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
              </div>
              
              <div className={`flex-1 ${msg.role === 'user' ? 'flex flex-col items-end' : ''}`}>
                <div className={`inline-block p-4 rounded-2xl max-w-[80%] ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : msg.isError
                    ? 'bg-red-50 text-red-900 border border-red-200'
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {msg.workflow_type && (
                    <div className="mt-2 pt-2 border-t border-gray-300/30">
                      <span className="text-xs opacity-75">Workflow: {msg.workflow_type}</span>
                    </div>
                  )}
                </div>
                <span className="text-xs text-gray-400 mt-1 block">
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div className="bg-gray-100 p-4 rounded-2xl">
                <Loader2 className="animate-spin text-gray-600" size={20} />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {messages.length === 1 && (
          <div className="px-6 pb-4">
            <p className="text-sm text-gray-500 mb-2">Preguntas rápidas:</p>
            <div className="grid grid-cols-2 gap-2">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(q)}
                  className="text-left text-sm p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="p-6 border-t bg-gray-50">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Escribe tu pregunta sobre Meta Ads..."
              disabled={loading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Powered by LangGraph + Meta Ads API
          </p>
        </div>
      </div>
    </div>
  );
}