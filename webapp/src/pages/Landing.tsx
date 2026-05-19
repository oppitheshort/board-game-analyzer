import { Link } from 'react-router-dom';
import { useAuth } from '../components/auth/AuthContext';

export function Landing() {
  const { token } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-dark-700 px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">Board Game Analyzer</h1>
        <nav className="flex gap-3">
          {token ? (
            <Link to="/dashboard" className="px-4 py-2 bg-emerald-500 text-black rounded-lg font-semibold text-sm hover:bg-emerald-400">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="px-4 py-2 bg-dark-700 rounded-lg text-sm hover:bg-dark-800">
                Login
              </Link>
              <Link to="/register" className="px-4 py-2 bg-emerald-500 text-black rounded-lg font-semibold text-sm hover:bg-emerald-400">
                Get Started
              </Link>
            </>
          )}
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        <h2 className="text-4xl font-bold mb-4 max-w-2xl">
          Real-time analysis for your board games
        </h2>
        <p className="text-gray-400 text-lg mb-8 max-w-xl">
          Watch momentum shifts, track player accuracy, and understand position evaluation — all in real-time as you play on Board Game Arena.
        </p>

        <div className="flex gap-4 mb-16">
          <Link to="/register" className="px-6 py-3 bg-emerald-500 text-black rounded-lg font-semibold hover:bg-emerald-400">
            Create Account
          </Link>
          <a href="#features" className="px-6 py-3 bg-dark-700 rounded-lg hover:bg-dark-800">
            Learn More
          </a>
        </div>

        <div id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full mb-16">
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 text-left">
            <div className="text-2xl mb-3">📊</div>
            <h3 className="font-semibold mb-2">Momentum Meter</h3>
            <p className="text-gray-400 text-sm">See who has the advantage and how it shifts with every move.</p>
          </div>
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 text-left">
            <div className="text-2xl mb-3">🎯</div>
            <h3 className="font-semibold mb-2">Move Quality</h3>
            <p className="text-gray-400 text-sm">Every move rated: Good, Inaccuracy, Mistake, or Blunder.</p>
          </div>
          <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 text-left">
            <div className="text-2xl mb-3">💪</div>
            <h3 className="font-semibold mb-2">Player Strength</h3>
            <p className="text-gray-400 text-sm">Track accuracy percentage for both players throughout the game.</p>
          </div>
        </div>

        <div className="bg-dark-800 border border-dark-700 rounded-xl p-8 max-w-2xl w-full mb-16">
          <h3 className="font-semibold text-lg mb-4">How It Works</h3>
          <ol className="text-left text-gray-400 text-sm space-y-3">
            <li className="flex gap-3">
              <span className="bg-emerald-500 text-black w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0">1</span>
              <span>Create your account and install the Chrome extension</span>
            </li>
            <li className="flex gap-3">
              <span className="bg-emerald-500 text-black w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0">2</span>
              <span>Log in through the extension popup</span>
            </li>
            <li className="flex gap-3">
              <span className="bg-emerald-500 text-black w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0">3</span>
              <span>Play a game on Board Game Arena — the sidebar appears automatically</span>
            </li>
            <li className="flex gap-3">
              <span className="bg-emerald-500 text-black w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0">4</span>
              <span>Watch real-time analysis as every move is evaluated</span>
            </li>
          </ol>
        </div>
      </main>

      <footer className="border-t border-dark-700 px-6 py-4 text-center text-gray-500 text-sm">
        Board Game Analyzer — Real-time analysis, not recommendations.
      </footer>
    </div>
  );
}
