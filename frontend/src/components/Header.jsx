import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FiUser, FiLogOut, FiAward } from 'react-icons/fi';
import { userAPI } from '../utils/api';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [profile, setProfile] = useState(null);
  const dropdownRef = useRef(null);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Fetch user profile
    const fetchProfile = async () => {
      try {
        const response = await userAPI.getProfile();
        setProfile(response.data);
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      }
    };

    if (user) {
      fetchProfile();
    }
  }, [user, location.pathname]); // Refetch when route changes

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowProfileDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="bg-white dark:bg-gray-800 shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/all-blogs" className="flex items-center">
            <img 
              src="/makemytrip-logo.png" 
              alt="MakeMyTrip" 
              className="h-10 w-auto"
              onError={(e) => {
                e.target.style.display = 'none';
                const fallback = e.target.nextElementSibling;
                if (fallback) fallback.style.display = 'flex';
              }}
            />
            {/* Fallback logo */}
            <div className="flex items-baseline gap-0" style={{ display: 'none' }}>
              <span className="text-2xl font-bold text-blue-900 dark:text-blue-700 lowercase">
                make
              </span>
              <div className="mx-1 bg-red-600 rounded-lg px-2 py-0.5 flex items-center justify-center">
                <span className="text-2xl font-bold text-white lowercase">
                  my
                </span>
              </div>
              <span className="text-2xl font-bold text-blue-900 dark:text-blue-700 lowercase">
                trip
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-4">
            <Link
              to="/all-blogs"
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                location.pathname === '/all-blogs'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              All Blogs
            </Link>
            <Link
              to="/my-blogs"
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                location.pathname === '/my-blogs'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              My Blogs
            </Link>
            <Link
              to="/create"
              className="btn-primary"
            >
              Create Blog
            </Link>

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Profile Dropdown */}
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-r from-primary-600 to-purple-600 text-white font-bold hover:shadow-lg transition-shadow"
              >
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </button>

              {showProfileDropdown && (
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-2 animate-slide-up">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <FiUser className="w-4 h-4" />
                      {profile?.username || user?.username || 'User'}
                    </p>
                  </div>
                  
                  <div className="px-4 py-3 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Blogs</span>
                      <span className="font-semibold text-primary-600 dark:text-primary-400">
                        {profile?.blogCount || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                        <FiAward className="w-4 h-4" />
                        Score
                      </span>
                      <span className="font-semibold text-purple-600 dark:text-purple-400">
                        {profile?.score || 0}
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 dark:border-gray-700 mt-2">
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-3 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2 transition-colors"
                    >
                      <FiLogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
