import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import SubscriptionList from './components/SubscriptionList';
import SubscriptionForm from './components/SubscriptionForm';
import DeliveryLogs from './components/DeliveryLogs';
import EditSubscriptionForm from './components/EditSubscriptionForm';
import WebhookTester from './components/WebhookTester';

function NavLink({ to, children }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link
      to={to}
      className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
        isActive 
          ? 'text-blue-600 border-b-2 border-blue-600' 
          : 'text-gray-500 hover:text-gray-900 hover:border-b-2 hover:border-gray-300'
      }`}
    >
      {children}
    </Link>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen h-full w-full flex flex-col bg-gray-50">
        <nav className="bg-white shadow-sm flex-none">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Link to="/" className="text-xl font-bold text-gray-800">
                    Webhook Manager
                  </Link>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <NavLink to="/">New Subscription</NavLink>
                  <NavLink to="/sub">Subscriptions</NavLink>
                  <NavLink to="/test">Test Webhook</NavLink>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="flex-1 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
          <Routes>
            <Route path="/sub" element={<SubscriptionList />} />
            <Route
              path="/"
              element={
                <SubscriptionForm
                  onSubscriptionAdded={() => {
                    window.location.href = '/';
                  }}
                />
              }
            />
            <Route path="/logs/:subscriptionId" element={<DeliveryLogs />} />
            <Route
              path="/edit/:subscriptionId"
              element={
                <EditSubscriptionForm
                  onSubscriptionUpdated={() => {
                    window.location.href = '/';
                  }}
                  onCancel={() => {
                    window.location.href = '/';
                  }}
                />
              }
            />
            <Route path="/test" element={<WebhookTester />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
