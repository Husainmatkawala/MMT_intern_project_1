import { useNavigate, useLocation } from 'react-router-dom';

const ChatbotButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Don't show on chatbot page itself
  if (location.pathname === '/chatbot') {
    return null;
  }

  const handleClick = () => {
    navigate('/chatbot');
  };

  return (
    <button
      onClick={handleClick}
      className="fixed bottom-6 right-6 z-40 w-20 h-20 rounded-full shadow-lg hover:shadow-2xl transition-all duration-300 flex items-center justify-center group hover:scale-110 active:scale-95 animate-pulse-slow bg-gradient-to-br from-cyan-400 to-blue-500"
      aria-label="Open Chatbot"
    >
      <img 
        src="/chat-bot.png" 
        alt="Chatbot" 
        className="w-16 h-16 object-contain group-hover:scale-110 transition-transform duration-200"
      />
      
      {/* Notification Badge (optional, can be used later) */}
      <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full border-2 border-white dark:border-gray-900 hidden">
        <span className="text-xs text-white font-bold"></span>
      </div>
    </button>
  );
};

export default ChatbotButton;
