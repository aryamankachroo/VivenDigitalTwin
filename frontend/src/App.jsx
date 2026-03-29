import { useEffect, useState } from 'react'
import axios from 'axios'
import Chat from './components/Chat'
import OAuth from './components/OAuth'

axios.defaults.withCredentials = true

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/auth/status')
        setIsAuthenticated(Boolean(response.data.authenticated))
      } catch (e) {
        setIsAuthenticated(false)
      }
    }
    checkAuth()
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <h1 className="mb-8 text-center text-4xl font-bold">My Digital Twin</h1>
        {!isAuthenticated && <OAuth onAuthSuccess={() => setIsAuthenticated(true)} />}
        <Chat isAuthenticated={isAuthenticated} />
      </div>
    </div>
  )
}

export default App
