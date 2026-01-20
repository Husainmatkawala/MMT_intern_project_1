import { useState, useEffect, useRef } from 'react';
import { FiSend, FiMessageSquare, FiUser, FiAlertCircle, FiSquare } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Header from '../components/Header';
import { chatbotAPI } from '../utils/api';

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const [streamedText, setStreamedText] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const streamingIntervalRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, streamedText]);

  // Cleanup streaming interval on unmount
  useEffect(() => {
    return () => {
      if (streamingIntervalRef.current) {
        clearInterval(streamingIntervalRef.current);
      }
    };
  }, []);

  // Welcome message on component mount
  useEffect(() => {
    const welcomeMessage = {
      id: Date.now(),
      text: "Hello! I'm your AI-powered MakeMyTrip travel assistant. I can help you plan trips, find hotels, restaurants, places to visit, and answer questions about destinations. How can I assist you today?",
      sender: 'bot',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages([welcomeMessage]);
    
    // Focus input field
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim()) return;

    const userMessageText = inputMessage;
    
    // Add user message
    const userMsg = {
      id: Date.now(),
      text: userMessageText,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setError(null);
    
    // Show typing indicator
    setIsTyping(true);
    
    try {
      // Call the chatbot API
      const response = await chatbotAPI.sendMessage(userMessageText, sessionId);
      
      if (response.data.success) {
        // Update session ID if new or changed
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
        
        const botResponseText = response.data.response;
        const botMsgId = Date.now() + 1;
        
        // Add empty bot message that will be streamed
        const botMsg = {
          id: botMsgId,
          text: '',
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          queryType: response.data.query_type,
          dataSource: response.data.data_source,
          isStreaming: true
        };
        
        setMessages(prev => [...prev, botMsg]);
        setStreamingMessageId(botMsgId);
        
        // Stream the text character by character
        let charIndex = 0;
        const streamSpeed = 8; // milliseconds per character (faster)
        
        streamingIntervalRef.current = setInterval(() => {
          if (charIndex < botResponseText.length) {
            const nextChunk = botResponseText.slice(0, charIndex + 1);
            setStreamedText(nextChunk);
            
            setMessages(prev => prev.map(msg => 
              msg.id === botMsgId 
                ? { ...msg, text: nextChunk }
                : msg
            ));
            
            charIndex++;
          } else {
            // Streaming complete
            clearInterval(streamingIntervalRef.current);
            setStreamingMessageId(null);
            setStreamedText('');
            
            // Mark streaming as complete
            setMessages(prev => prev.map(msg => 
              msg.id === botMsgId 
                ? { ...msg, text: botResponseText, isStreaming: false }
                : msg
            ));
          }
        }, streamSpeed);
        
      } else {
        throw new Error(response.data.error || 'Failed to get response');
      }
    } catch (err) {
      console.error('Chatbot API error:', err);
      
      // Determine error message
      let errorMessage = "I'm having trouble connecting to the travel assistant service. ";
      
      if (err.response?.status === 500) {
        errorMessage += "Please try again in a moment.";
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        errorMessage += "The service might be temporarily unavailable. Please check if it's running.";
      } else {
        errorMessage += err.response?.data?.error || err.message || "Please try again.";
      }
      
      // Add error message as bot message
      const errorMsg = {
        id: Date.now() + 1,
        text: errorMessage,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMsg]);
      setError(errorMessage);
    } finally {
      setIsTyping(false);
    }
  };

  const handleStopGenerating = () => {
    if (streamingIntervalRef.current) {
      clearInterval(streamingIntervalRef.current);
      streamingIntervalRef.current = null;
    }
    
    // Mark the message as complete with current text and enable input
    if (streamingMessageId) {
      setMessages(prev => prev.map(msg => 
        msg.id === streamingMessageId 
          ? { ...msg, isStreaming: false }
          : msg
      ));
      setStreamingMessageId(null);
      setStreamedText('');
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex flex-col">
      <Header />
      
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 py-6">
        {/* Chat Header */}
        <div className="section-card mb-4 animate-slide-up">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-primary-600 to-purple-600 dark:from-primary-500 dark:to-purple-500 rounded-full flex items-center justify-center">
              <FiMessageSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 dark:from-primary-400 dark:to-purple-400 bg-clip-text text-transparent">
                Travel Assistant
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Ask me anything about your travel plans
              </p>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 section-card overflow-y-auto space-y-4 mb-4 animate-fade-in" style={{ maxHeight: 'calc(100vh - 350px)' }}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
            >
              <div className={`flex gap-3 max-w-[80%] ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.sender === 'user' 
                    ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
                    : 'bg-gradient-to-r from-gray-400 to-gray-500 dark:from-gray-600 dark:to-gray-700'
                }`}>
                  {message.sender === 'user' ? (
                    <FiUser className="w-4 h-4 text-white" />
                  ) : (
                    <FiMessageSquare className="w-4 h-4 text-white" />
                  )}
                </div>
                
                {/* Message Bubble */}
                <div>
                  <div className={`rounded-2xl px-4 py-3 ${
                    message.sender === 'user'
                      ? 'bg-gradient-to-r from-primary-600 to-blue-600 text-white'
                      : message.isError
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border border-red-300 dark:border-red-700'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100'
                  } shadow-md`}>
                    {message.isError && (
                      <div className="flex items-center gap-2 mb-2">
                        <FiAlertCircle className="w-4 h-4" />
                        <span className="text-xs font-semibold">Error</span>
                      </div>
                    )}
                    {message.sender === 'bot' && !message.isError ? (
                      <div className="chatbot-message">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.text}
                        </ReactMarkdown>
                        {message.isStreaming && (
                          <span className="inline-block w-2 h-4 bg-gray-600 dark:bg-gray-400 ml-1 animate-pulse"></span>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-line leading-relaxed">{message.text}</p>
                    )}
                  </div>
                  <div className={`flex items-center gap-2 mt-1 ${
                    message.sender === 'user' ? 'justify-end' : 'justify-start'
                  }`}>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {message.timestamp}
                    </p>
                    {message.queryType && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        {message.queryType}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start animate-slide-up">
              <div className="flex gap-3 max-w-[80%]">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-gray-400 to-gray-500 dark:from-gray-600 dark:to-gray-700 flex items-center justify-center">
                  <FiMessageSquare className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-4 py-3 shadow-md">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="section-card animate-slide-up">
          {/* Stop Generating Button */}
          {streamingMessageId && (
            <div className="mb-3 flex justify-center">
              <button
                onClick={handleStopGenerating}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center gap-2 font-semibold transition-all duration-200 shadow-md hover:shadow-lg"
              >
                <FiSquare className="w-4 h-4" />
                Stop Generating
              </button>
            </div>
          )}
          
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="form-input flex-1"
              disabled={isTyping || streamingMessageId !== null}
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isTyping || streamingMessageId !== null}
              className="btn-primary px-6 py-3 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FiSend className="w-5 h-5" />
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 text-center">
            Powered by AI • Ask about destinations, hotels, restaurants, or plan your trip
          </p>
          {sessionId && (
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-1">
              Session active • Your conversation is remembered
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
