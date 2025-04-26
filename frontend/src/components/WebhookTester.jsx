import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function WebhookTester() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [selectedSubscription, setSelectedSubscription] = useState('');
  const [eventData, setEventData] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [deliveryId, setDeliveryId] = useState(null);
  const [deliveryStatus, setDeliveryStatus] = useState(null);

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      const response = await api.get('/subscriptions');
      setSubscriptions(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError('Failed to fetch subscriptions');
      console.error('Error fetching subscriptions:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setDeliveryId(null);
    setDeliveryStatus(null);

    if (!selectedSubscription) {
      setError('Please select a subscription');
      return;
    }

    try {
      setLoading(true);
      let parsedData;
      try {
        parsedData = JSON.parse(eventData);
      } catch (parseError) {
        console.error('Error parsing JSON:', parseError);
        setError('Invalid JSON data');
        setLoading(false);
        return;
      }

      // Ensure the payload matches the expected structure
      const payload = {
        event_type: parsedData.event_type || 'test_event',
        data: parsedData.data || parsedData
      };

      // Validate payload before sending
      if (!payload.event_type || typeof payload.event_type !== 'string') {
        setError('event_type must be a string');
        setLoading(false);
        return;
      }

      const response = await api.post(`/ingest/${selectedSubscription}`, payload);

      setSuccess('Webhook sent successfully');
      setDeliveryId(response.data.delivery_id);
      
      // Start polling for delivery status
      pollDeliveryStatus(response.data.delivery_id);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 
                          (typeof err.response?.data === 'object' ? JSON.stringify(err.response.data) : err.response?.data) ||
                          err.message ||
                          'Failed to send webhook';
      setError(errorMessage);
      console.error('Error sending webhook:', err);
    } finally {
      setLoading(false);
    }
  };

  const pollDeliveryStatus = async (id) => {
    let attempts = 0;
    const maxAttempts = 10;
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/deliveries/${id}`);
        setDeliveryStatus(response.data);
        
        if (response.data.status !== 'pending' || attempts >= maxAttempts) {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error polling delivery status:', err);
        clearInterval(interval);
      }
      attempts++;
    }, 1000);
  };

  const handleViewHistory = async () => {
    if (!deliveryId) return;
    
    try {
      const response = await api.get(`/deliveries/${deliveryId}/history`);
      setDeliveryStatus(response.data);
    } catch (err) {
      setError('Failed to fetch delivery history');
      console.error('Error fetching delivery history:', err);
    }
  };

  // Helper function to format error messages
  const formatError = (error) => {
    if (typeof error === 'string') return error;
    if (error?.msg) return error.msg;
    if (Array.isArray(error)) return error.map(e => e.msg || String(e)).join(', ');
    return String(error);
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-semibold mb-6 text-gray-900">Test Webhook Delivery</h1>
      
      <form onSubmit={handleSubmit} className="bg-white shadow-sm border border-gray-200 rounded-lg p-6 mb-6">
        <div className="space-y-6">
          <div>
            <label htmlFor="subscription" className="block text-sm font-medium text-gray-900 mb-1">
              Select Subscription
            </label>
            <select
              id="subscription"
              value={selectedSubscription}
              onChange={(e) => setSelectedSubscription(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 shadow-sm sm:text-sm rounded-md"
            >
              <option value="" className="text-gray-900 bg-white">Select a subscription...</option>
              {subscriptions.map((sub) => (
                <option key={sub.id} value={sub.id} className="text-gray-900 bg-white">
                  {sub.target_url} ({sub.event_types.join(', ')})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="eventData" className="block text-sm font-medium text-gray-900 mb-1">
              Event Data (JSON)
            </label>
            <textarea
              id="eventData"
              rows={8}
              value={eventData}
              onChange={(e) => setEventData(e.target.value)}
              placeholder={JSON.stringify({
                event_type: "test_event",
                data: {
                  key: "value"
                }
              }, null, 2)}
              className="mt-1 block w-full shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm border border-gray-300 rounded-md font-mono bg-white p-3 text-gray-900"
            />
          </div>

          {error && (
            <div className="rounded-md bg-white border border-red-200 p-4">
              <div className="text-sm text-red-800">{formatError(error)}</div>
            </div>
          )}

          {success && (
            <div className="rounded-md bg-white border border-green-200 p-4">
              <div className="text-sm text-green-800">{success}</div>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-gray-900 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? 'Sending...' : 'Send Webhook'}
            </button>
          </div>
        </div>
      </form>

      {deliveryStatus && (
        <div className="bg-white shadow-sm border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Delivery Status</h2>
            <button
              onClick={handleViewHistory}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              View Full History
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Status</h3>
              <p className={`mt-1 font-medium ${
                deliveryStatus.status === 'DELIVERED' ? 'text-green-700' : 'text-red-700'
              }`}>
                {deliveryStatus.status}
              </p>
            </div>

            {deliveryStatus.attempts && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Attempts</h3>
                <div className="space-y-3">
                  {deliveryStatus.attempts.map((attempt, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="flex justify-between items-center mb-2">
                        <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                          attempt.status === 'DELIVERED' 
                            ? 'bg-white text-green-800 border border-green-200' 
                            : 'bg-white text-red-800 border border-red-200'
                        }`}>
                          {attempt.status}
                        </span>
                        <span className="text-sm text-gray-600">
                          {new Date(attempt.last_attempt).toLocaleString()}
                        </span>
                      </div>
                      {attempt.response_status && (
                        <p className="text-sm text-gray-700 mb-1">
                          Response Code: {attempt.response_status}
                        </p>
                      )}
                      {attempt.error_message && (
                        <p className="text-sm text-red-700 mt-1 bg-white border border-red-200 p-2 rounded">
                          Error: {attempt.error_message}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 