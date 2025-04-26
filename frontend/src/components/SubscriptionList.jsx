import { useState, useEffect } from 'react';
import axios from 'axios';
import { TrashIcon, EyeIcon } from '@heroicons/react/24/outline';

export default function SubscriptionList() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/subscriptions');
      setSubscriptions(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch subscriptions');
      console.error('Error fetching subscriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteSubscription = async (id) => {
    try {
      await axios.delete(`/api/subscriptions/${id}`);
      setSubscriptions(subscriptions.filter(sub => sub.id !== id));
    } catch (err) {
      setError('Failed to delete subscription');
      console.error('Error deleting subscription:', err);
    }
  };

  if (loading) return <div className="text-center py-4">Loading...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Webhook Subscriptions</h2>
      <div className="bg-white shadow rounded-lg divide-y">
        {subscriptions.length === 0 ? (
          <p className="p-4 text-gray-500">No subscriptions found</p>
        ) : (
          subscriptions.map((subscription) => (
            <div key={subscription.id} className="p-4 flex items-center justify-between">
              <div>
                <h3 className="font-medium">{subscription.name || subscription.url}</h3>
                <p className="text-sm text-gray-500">{subscription.url}</p>
                <div className="text-sm text-gray-500">
                  Status: <span className={`font-medium ${subscription.active ? 'text-green-600' : 'text-red-600'}`}>
                    {subscription.active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => window.location.href = `/logs/${subscription.id}`}
                  className="p-2 text-gray-600 hover:text-blue-600"
                  title="View Logs"
                >
                  <EyeIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => deleteSubscription(subscription.id)}
                  className="p-2 text-gray-600 hover:text-red-600"
                  title="Delete Subscription"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
} 