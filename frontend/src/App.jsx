import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import SubscriptionList from './components/SubscriptionList';
import SubscriptionForm from './components/SubscriptionForm';
import DeliveryLogs from './components/DeliveryLogs';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Link to="/" className="text-xl font-bold text-gray-800">
                    Webhook Manager
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route
              path="/"
              element={
                <div className="space-y-8">
                  <SubscriptionForm
                    onSubscriptionAdded={(newSubscription) => {
                      // Force a refresh of the subscription list
                      window.location.reload();
                    }}
                  />
                  <SubscriptionList />
                </div>
              }
            />
            <Route path="/logs/:subscriptionId" element={<DeliveryLogs />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
