'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertCircle, CheckCircle, Bot, User, Moon, Sun, TrendingUp, DollarSign, Target, BarChart3 } from 'lucide-react';

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
  const [darkMode, setDarkMode] = useState(false);
  const [showStats, setShowStats] = useState(true);
  // ✅ CAMBIO: threadId ahora se actualiza con la respuesta del backend
  const [threadId, setThreadId] = useState<string | null>(null);
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
          // ✅ CAMBIO: Enviar threadId solo si existe
          ...(threadId && { thread_id: threadId }),
          user_id: 'demo_user'
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      
      // ✅ CAMBIO CRÍTICO: Usar data.response en lugar de data.content
      let messageContent = data.response;
      
      // ✅ CAMBIO: Si response es un objeto con type/text, extraer el texto
      if (typeof messageContent === 'object' && messageContent.type === 'text') {
        messageContent = messageContent.text;
      }
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: messageContent,
        workflow_type: data.workflow_type,
        metadata: data.metadata,
        timestamp: new Date(data.timestamp || new Date())
      };

      // ✅ CAMBIO: Guardar el thread_id para próximas queries
      if (data.thread_id) {
        setThreadId(data.thread_id);
      }

      setMessages(prev => [...prev, assistantMessage]);
      setStatus({ type: 'success', message: 'Respuesta recibida' });
    } catch (error) {
      console.error('Error completo:', error);
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

  const quickQuestions = [
    "Lista todas las campañas",
    "TOP 3 anuncios de Baqueira",
    "¿Cuál fue el gasto esta semana?",
    "Dame recomendaciones"
  ];

  const stats = [
    { icon: DollarSign, label: 'Gasto Hoy', value: '€342.50', change: '+12%', color: 'blue' },
    { icon: Target, label: 'CPA Promedio', value: '€15.30', change: '-8%', color: 'green' },
    { icon: TrendingUp, label: 'Conversiones', value: '23', change: '+15%', color: 'purple' },
    { icon: BarChart3, label: 'CTR', value: '2.4%', change: '+0.3%', color: 'orange' }
  ];

  const bgClass = darkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50';
  const cardClass = darkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white';
  const textClass = darkMode ? 'text-white' : 'text-gray-900';
  const secondaryTextClass = darkMode ? 'text-gray-400' : 'text-gray-500';

  return (
    <div className={`min-h-screen ${bgClass} flex transition-colors duration-300`}>
      
      {/* Sidebar de Estadísticas */}
      {showStats && (
        <div className={`w-80 ${cardClass} border-r p-6 space-y-6 transition-all duration-300`}>
          <div className="flex items-center justify-between">
            <h2 className={`text-lg font-bold ${textClass}`}>Dashboard</h2>
            <button
              onClick={() => setShowStats(false)}
              className={`${secondaryTextClass} hover:${textClass} transition-colors`}
            >
              ←
            </button>
          </div>

          <div className="space-y-4">
            {stats.map((stat, idx) => {
              const Icon = stat.icon;
              const colorClass = {
                blue: 'bg-blue-100 text-blue-600',
                green: 'bg-green-100 text-green-600',
                purple: 'bg-purple-100 text-purple-600',
                orange: 'bg-orange-100 text-orange-600'
              }[stat.color];

              return (
                <div key={idx} className={`${darkMode ? 'bg-gray-700/50' : 'bg-gray-50'} p-4 rounded-xl`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-2 rounded-lg ${colorClass}`}>
                      <Icon size={20} />
                    </div>
                    <span className={`text-sm ${secondaryTextClass}`}>{stat.label}</span>
                  </div>
                  <div className="flex items-end justify-between">
                    <span className={`text-2xl font-bold ${textClass}`}>{stat.value}</span>
                    <span className={`text-sm ${stat.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                      {stat.change}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ✅ CAMBIO: Mostrar thread_id actual */}
          <div className={`${darkMode ? 'bg-gradient-to-r from-blue-900/50 to-purple-900/50' : 'bg-gradient-to-r from-blue-50 to-purple-50'} p-4 rounded-xl border ${darkMode ? 'border-blue-800' : 'border-blue-100'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Bot size={16} className="text-blue-600" />
              <span className={`text-sm font-semibold ${textClass}`}>Estado del Agente</span>
            </div>
            <p className={`text-xs ${secondaryTextClass}`}>
              Thread: {threadId ? threadId.slice(0, 20) + '...' : 'No iniciado'}
            </p>
            <p className={`text-xs ${secondaryTextClass} mt-1`}>
              Mensajes: {messages.length}
            </p>
            {/* ✅ NUEVO: Botón para reiniciar conversación */}
            {threadId && (
              <button
                onClick={() => {
                  setThreadId(null);
                  setMessages([{ role: 'assistant', content: '¡Nueva conversación iniciada! ¿En qué puedo ayudarte?', timestamp: new Date() }]);
                }}
                className="mt-2 text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg transition-colors"
              >
                Nueva conversación
              </button>
            )}
          </div>
        </div>
      )}

      {/* Chat Principal */}
      <div className="flex-1 flex flex-col">
        
        {/* Header */}
        <div className={`${darkMode ? 'bg-gradient-to-r from-gray-800 to-gray-900' : 'bg-gradient-to-r from-blue-600 to-purple-600'} text-white p-6 shadow-lg`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {!showStats && (
                <button
                  onClick={() => setShowStats(true)}
                  className="bg-white/10 p-2 rounded-lg hover:bg-white/20 transition-colors"
                >
                  →
                </button>
              )}
              <div className="bg-white/20 p-3 rounded-full backdrop-blur-sm">
                <Bot size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Meta Ads Agent</h1>
                <p className="text-sm text-blue-100">Asistente inteligente con LangGraph</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="bg-white/10 p-2 rounded-lg hover:bg-white/20 transition-colors"
              >
                {darkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              
              <div className="flex items-center gap-2 bg-white/10 px-3 py-2 rounded-full backdrop-blur-sm">
                {status.type === 'success' && <CheckCircle size={16} className="text-green-300" />}
                {status.type === 'error' && <AlertCircle size={16} className="text-red-300" />}
                {status.type === 'warning' && <AlertCircle size={16} className="text-yellow-300" />}
                <span className="text-sm">{status.message || 'Verificando...'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Mensajes */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
                  : 'bg-gradient-to-br from-blue-500 to-cyan-500'
              }`}>
                {msg.role === 'user' ? <User size={18} className="text-white" /> : <Bot size={18} className="text-white" />}
              </div>
              
              <div className={`flex-1 ${msg.role === 'user' ? 'flex flex-col items-end' : ''}`}>
                <div className={`inline-block p-4 rounded-2xl max-w-[85%] shadow-md ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : msg.isError
                    ? darkMode ? 'bg-red-900/50 text-red-200 border border-red-700' : 'bg-red-50 text-red-900 border border-red-200'
                    : darkMode ? 'bg-gray-700 text-gray-100' : 'bg-gray-100 text-gray-900'
                }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {msg.workflow_type && (
                    <div className="mt-3 pt-3 border-t border-white/20">
                      <span className="text-xs opacity-75 font-mono">⚡ {msg.workflow_type}</span>
                    </div>
                  )}
                </div>
                <span className={`text-xs ${secondaryTextClass} mt-1 block`}>
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-3 animate-in fade-in duration-300">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg">
                <Bot size={18} className="text-white" />
              </div>
              <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-2xl shadow-md`}>
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Questions */}
        {messages.length === 1 && (
          <div className="px-6 pb-4">
            <p className={`text-sm ${secondaryTextClass} mb-3 font-medium`}>⚡ Preguntas rápidas:</p>
            <div className="grid grid-cols-2 gap-2">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(q)}
                  className={`text-left text-sm p-3 rounded-lg transition-all border-2 hover:scale-105 ${
                    darkMode 
                      ? 'bg-gray-700 hover:bg-gray-600 border-gray-600' 
                      : 'bg-white hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className={`p-6 border-t ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Pregúntame sobre tus campañas de Meta Ads..."
              disabled={loading}
              className={`flex-1 px-4 py-3 border-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all ${
                darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900'
              }`}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg hover:shadow-xl hover:scale-105"
            >
              {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </div>
          <div className="flex items-center justify-between mt-3">
            <p className={`text-xs ${secondaryTextClass}`}>
              🚀 Powered by LangGraph + Render
            </p>
            <p className={`text-xs ${secondaryTextClass}`}>
              {messages.length} mensajes {threadId && `• Thread activo`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}