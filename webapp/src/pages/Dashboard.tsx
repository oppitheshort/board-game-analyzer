import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../components/auth/AuthContext';

export function Dashboard() {
  const { user, token, loading, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !token) navigate('/login');
  }, [loading, token, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen">
      <header className="border-b border-dark-700 px-6 py-4 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">Board Game Analyzer</Link>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{user.email}</span>
          <button
            onClick={() => { logout(); navigate('/'); }}
            className="px-3 py-1.5 bg-dark-700 rounded-lg text-sm hover:bg-red-500/20 hover:text-red-400"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6">
            <h3 className="font-semibold mb-4">Getting Started</h3>
            <ol className="text-gray-400 text-sm space-y-3">
              <li className="flex gap-2">
                <span className="text-emerald-500 font-bold">1.</span>
                Install the Chrome extension
              </li>
              <li className="flex gap-2">
                <span className="text-emerald-500 font-bold">2.</span>
                Click the extension icon and log in with your account
              </li>
              <li className="flex gap-2">
                <span className="text-emerald-500 font-bold">3.</span>
                Navigate to a Connect Four game on Board Game Arena
              </li>
              <li className="flex gap-2">
                <span className="text-emerald-500 font-bold">4.</span>
                The analysis sidebar will appear automatically
              </li>
            </ol>
          </div>

          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6">
            <h3 className="font-semibold mb-4">Account</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Email</span>
                <span>{user.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Member since</span>
                <span>{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 md:col-span-2">
            <h3 className="font-semibold mb-4">Supported Games</h3>
            <div className="flex gap-3">
              <span className="px-3 py-1.5 bg-emerald-500/10 text-emerald-500 rounded-lg text-sm font-medium">
                Connect Four
              </span>
              <span className="px-3 py-1.5 bg-dark-700 text-gray-500 rounded-lg text-sm">
                More coming soon
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
