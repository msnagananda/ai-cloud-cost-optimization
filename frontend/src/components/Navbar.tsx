import { Link, useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()
  const email = localStorage.getItem('email')

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('email')
    navigate('/login')
  }

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <Link to="/" className="text-lg font-semibold text-white tracking-tight">
        ☁️ Cost Detective
      </Link>
      <div className="flex items-center gap-6 text-sm">
        <Link to="/" className="text-gray-400 hover:text-white transition-colors">Dashboard</Link>
        <Link to="/history" className="text-gray-400 hover:text-white transition-colors">History</Link>
        <span className="text-gray-600">{email}</span>
        <button
          onClick={logout}
          className="text-gray-400 hover:text-red-400 transition-colors"
        >
          Sign out
        </button>
      </div>
    </nav>
  )
}
