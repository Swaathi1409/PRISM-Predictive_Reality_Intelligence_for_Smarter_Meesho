import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Mail, Lock, User, ArrowRight, Activity, Zap, LockKeyhole } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      navigate('/chat');
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex">
      {/* Left side - Dynamic branding & value props */}
      <div className="hidden lg:flex w-1/2 bg-zinc-950 p-12 flex-col justify-between border-r border-white/10 relative overflow-hidden">
        
        {/* Animated background elements */}
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-fuchsia-600/20 rounded-full blur-[128px] animate-pulse"></div>
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-blue-600/20 rounded-full blur-[128px] animate-pulse" style={{ animationDelay: '2s' }}></div>

        <div className="z-10 relative">
          <div className="flex items-center gap-3 text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-fuchsia-400 to-blue-400 mb-16">
            <Sparkles className="w-8 h-8 text-fuchsia-400" />
            PRISM
          </div>

          <h1 className="text-5xl font-light leading-tight mb-6">
            Predictive Reality<br />
            Intelligence for<br />
            <span className="font-semibold bg-clip-text text-transparent bg-gradient-to-r from-fuchsia-400 to-blue-400">
              Smarter Meesho.
            </span>
          </h1>
          
          <p className="text-zinc-400 text-lg max-w-md mb-12">
            The AI commerce brain that understands your life events, cultural context, and personal preferences to find exactly what you need.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-6 z-10 relative">
          <div className="bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur-sm">
            <Activity className="w-8 h-8 text-fuchsia-400 mb-4" />
            <h3 className="font-medium text-white mb-2">Memory Mining</h3>
            <p className="text-sm text-zinc-400">PRISM learns your preferences over time to personalize every recommendation.</p>
          </div>
          <div className="bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur-sm">
            <Zap className="w-8 h-8 text-blue-400 mb-4" />
            <h3 className="font-medium text-white mb-2">4-Agent Debate</h3>
            <p className="text-sm text-zinc-400">Kismat, Paisa, Samay, and Soch evaluate every product before you see it.</p>
          </div>
        </div>
      </div>

      {/* Right side - Auth Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative">
        {/* Mobile background */}
        <div className="lg:hidden absolute inset-0 bg-gradient-to-br from-fuchsia-900/20 to-blue-900/20 z-0"></div>

        <div className="w-full max-w-md z-10">
          <div className="lg:hidden flex items-center gap-3 text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-fuchsia-400 to-blue-400 mb-12 justify-center">
            <Sparkles className="w-8 h-8 text-fuchsia-400" />
            PRISM
          </div>

          <div className="mb-10 text-center lg:text-left">
            <h2 className="text-3xl font-semibold text-white mb-2">
              {isLogin ? 'Welcome back' : 'Create your account'}
            </h2>
            <p className="text-zinc-400">
              {isLogin ? 'Enter your details to access your PRISM memory.' : 'Start your personalized shopping journey.'}
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
              <div className="text-red-400 font-medium text-sm">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Full Name</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-zinc-500" />
                  </div>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 bg-zinc-900/50 border border-white/10 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent transition-all"
                    placeholder="Enter your name"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-zinc-500" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-zinc-900/50 border border-white/10 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent transition-all"
                  placeholder="name@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-zinc-500" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 bg-zinc-900/50 border border-white/10 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-transparent transition-all"
                  placeholder="••••••••"
                  minLength={6}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-fuchsia-600 to-blue-600 hover:from-fuchsia-500 hover:to-blue-500 text-white rounded-xl font-medium transition-all flex items-center justify-center gap-2 mt-8 disabled:opacity-50 disabled:cursor-not-allowed group shadow-[0_0_20px_rgba(192,38,211,0.3)] hover:shadow-[0_0_30px_rgba(192,38,211,0.5)]"
            >
              {isLoading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-zinc-400 text-sm">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
                className="text-fuchsia-400 hover:text-fuchsia-300 font-medium transition-colors"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
