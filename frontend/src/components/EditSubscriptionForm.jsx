import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function EditSubscriptionForm({ subscriptionId, onSubscriptionUpdated, onCancel }) {
  const [formData, setFormData] = useState({
    target_url: '',
    event_types: '',
    secret: ''
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const response = await api.get(`/api/subscriptions/${subscriptionId}`);
        const subscription = response.data;
        setFormData({
          target_url: subscription.target_url,
          event_types: subscription.event_types.join(','),
          secret: subscription.secret || ''
        });
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch subscription details');
        console.error('Error fetching subscription:', err);
      }
    };

    fetchSubscription();
  }, [subscriptionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const event_types = formData.event_types.split(',').map(event => event.trim()).filter(Boolean);
      
      const response = await api.put(`/api/subscriptions/${subscriptionId}`, {
        target_url: formData.target_url,
        event_types,
        secret: formData.secret || undefined
      });

      onSubscriptionUpdated(response.data);
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to update subscription');
      console.error('Error updating subscription:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  const inputClasses = "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 placeholder-gray-400";

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <form onSubmit={handleSubmit}>
        <h2 className="text-xl font-semibold mb-6">Edit Subscription</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="target_url" className="block text-sm font-medium text-gray-700">
              Webhook URL *
            </label>
            <input
              type="url"
              id="target_url"
              name="target_url"
              required
              value={formData.target_url}
              onChange={handleChange}
              className={inputClasses}
              placeholder="https://example.com/webhook"
            />
          </div>

          <div>
            <label htmlFor="event_types" className="block text-sm font-medium text-gray-700">
              Event Types (comma-separated) *
            </label>
            <input
              type="text"
              id="event_types"
              name="event_types"
              required
              value={formData.event_types}
              onChange={handleChange}
              className={inputClasses}
              placeholder="event1,event2,event3"
            />
          </div>

          <div>
            <label htmlFor="secret" className="block text-sm font-medium text-gray-700">
              Secret (Optional)
            </label>
            <input
              type="password"
              id="secret"
              name="secret"
              value={formData.secret}
              onChange={handleChange}
              className={inputClasses}
              placeholder="Webhook secret for signature verification"
            />
          </div>
        </div>

        {error && (
          <div className="mt-4 text-red-500 text-sm">{error}</div>
        )}

        <div className="mt-6 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-black bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Save Changes
          </button>
        </div>
      </form>
    </div>
  );
} 