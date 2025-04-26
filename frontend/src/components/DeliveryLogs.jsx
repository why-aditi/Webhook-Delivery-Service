import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

export default function DeliveryLogs() {
  const { subscriptionId } = useParams();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    fetchLogs();
    fetchSubscription();
  }, [subscriptionId]);

  const fetchSubscription = async () => {
    try {
      const response = await axios.get(`/api/subscriptions/${subscriptionId}`);
      setSubscription(response.data);
    } catch (err) {
      console.error('Error fetching subscription:', err);
    }
  };

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/subscriptions/${subscriptionId}/logs`);
      setLogs(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch delivery logs');
      console.error('Error fetching logs:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-4">Loading...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;

  return (
    <div className="space-y-4">
      {subscription && (
        <div className="bg-white p-4 rounded-lg shadow mb-4">
          <h2 className="text-xl font-semibold">Subscription Details</h2>
          <p className="text-gray-600">{subscription.name || subscription.url}</p>
          <p className="text-sm text-gray-500">{subscription.url}</p>
        </div>
      )}

      <h2 className="text-xl font-semibold">Delivery Logs</h2>
      <div className="bg-white shadow rounded-lg divide-y">
        {logs.length === 0 ? (
          <p className="p-4 text-gray-500">No delivery logs found</p>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-1 rounded-full text-sm ${
                  log.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {log.status}
                </span>
                <span className="text-sm text-gray-500">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
              
              <div className="space-y-2">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Event</h4>
                  <p className="text-sm text-gray-600">{log.event}</p>
                </div>

                {log.response_code && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Response Code</h4>
                    <p className="text-sm text-gray-600">{log.response_code}</p>
                  </div>
                )}

                {log.response_body && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Response Body</h4>
                    <pre className="text-sm text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto">
                      {typeof log.response_body === 'string' ? log.response_body : JSON.stringify(log.response_body, null, 2)}
                    </pre>
                  </div>
                )}

                {log.error && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Error</h4>
                    <p className="text-sm text-red-600">{log.error}</p>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
} 