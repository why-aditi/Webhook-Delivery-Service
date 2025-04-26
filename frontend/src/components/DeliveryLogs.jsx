import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import api from '../utils/api';

export default function DeliveryLogs() {
  const { subscriptionId } = useParams();
  const [deliveries, setDeliveries] = useState([]);
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [deliveryHistory, setDeliveryHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [subscription, setSubscription] = useState(null);

  const fetchSubscription = useCallback(async () => {
    try {
      const response = await api.get(`/subscriptions/${subscriptionId}`);
      setSubscription(response.data);
    } catch (err) {
      console.error('Error fetching subscription:', err);
      setError('Failed to fetch subscription details');
    }
  }, [subscriptionId]);

  const fetchDeliveries = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`/subscriptions/${subscriptionId}/deliveries`);
      setDeliveries(response.data.deliveries || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch deliveries');
      console.error('Error fetching deliveries:', err);
      setDeliveries([]);
    } finally {
      setLoading(false);
    }
  }, [subscriptionId]);

  const fetchDeliveryHistory = async (deliveryId) => {
    try {
      const response = await api.get(`/deliveries/${deliveryId}/history`);
      setDeliveryHistory(response.data);
    } catch (err) {
      console.error('Error fetching delivery history:', err);
      setError('Failed to fetch delivery history');
    }
  };

  useEffect(() => {
    fetchSubscription();
    fetchDeliveries();
  }, [fetchSubscription, fetchDeliveries]);

  const handleDeliveryClick = async (delivery) => {
    setSelectedDelivery(delivery);
    await fetchDeliveryHistory(delivery.id);
  };

  if (loading) return <div className="h-full w-full flex items-center justify-center">Loading...</div>;
  if (error) return <div className="h-full w-full flex items-center justify-center text-red-500">{error}</div>;

  return (
    <div className="h-full w-full flex flex-col space-y-6">
      {subscription && (
        <div className="w-full bg-white p-6 rounded-lg shadow flex-none">
          <h2 className="text-2xl font-semibold mb-4">Subscription Details</h2>
          <p className="text-lg text-gray-600">Target URL: {subscription.target_url}</p>
          <p className="text-base text-gray-500">Event Types: {subscription.event_types.join(', ')}</p>
        </div>
      )}

      <div className="flex-1 flex flex-col min-h-0">
        <h2 className="text-2xl font-semibold mb-4 flex-none">Delivery Logs</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Deliveries List */}
          <div className="bg-white shadow rounded-lg overflow-auto">
            <div className="divide-y">
              {deliveries.length === 0 ? (
                <div className="p-6 text-center text-gray-500">No deliveries found</div>
              ) : (
                deliveries.map((delivery) => (
                  <div
                    key={delivery.id}
                    onClick={() => handleDeliveryClick(delivery)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 ${
                      selectedDelivery?.id === delivery.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                        delivery.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {delivery.status}
                      </span>
                      <span className="text-sm text-gray-500">
                        {new Date(delivery.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">Event Type: {delivery.event_type}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Delivery History */}
          <div className="bg-white shadow rounded-lg overflow-auto">
            {!selectedDelivery ? (
              <div className="p-6 text-center text-gray-500">
                Select a delivery to view its history
              </div>
            ) : (
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4">Delivery History</h3>
                {deliveryHistory ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700">Status</h4>
                        <p className="text-base text-gray-600">{deliveryHistory.status}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-700">Attempts</h4>
                        <p className="text-base text-gray-600">{deliveryHistory.attempts.length}</p>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-700">Attempt History</h4>
                      <div className="mt-2 space-y-3">
                        {deliveryHistory.attempts.map((attempt, index) => (
                          <div key={index} className="border rounded-lg p-3">
                            <div className="flex justify-between items-center mb-2">
                              <span className={`px-2 py-1 rounded-full text-sm font-medium ${
                                attempt.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {attempt.success ? 'Success' : 'Failed'}
                              </span>
                              <span className="text-sm text-gray-500">
                                {new Date(attempt.timestamp).toLocaleString()}
                              </span>
                            </div>
                            {attempt.response_code && (
                              <p className="text-sm text-gray-600">
                                Response Code: {attempt.response_code}
                              </p>
                            )}
                            {attempt.error && (
                              <p className="text-sm text-red-600 mt-1">
                                Error: {attempt.error}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500">Loading history...</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 