import { useState } from 'react';
import api from '../utils/api';

export default function SubscriptionForm({ onSubscriptionAdded }) {
  const [formData, setFormData] = useState({
    target_url: '',
    event_types: '',
    secret: ''
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Split event_types into array
      const event_types = formData.event_types.split(',').map(event => event.trim()).filter(Boolean);

      const response = await api.post('/api/subscriptions', {
        target_url: formData.target_url,
        event_types,
        secret: formData.secret || undefined // Only include if not empty
      });

      setFormData({ target_url: '', event_types: '', secret: '' });
      onSubscriptionAdded(response.data);
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to create subscription');
      console.error('Error creating subscription:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const inputClasses = "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 placeholder-gray-400";

  return (
    <div className="w-full bg-white rounded-lg shadow">
      <form onSubmit={handleSubmit} className="p-6 sm:p-8">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900">Add New Subscription</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="target_url" className="block text-sm font-medium text-gray-700">Webhook URL *</label>
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
            <label htmlFor="event_types" className="block text-sm font-medium text-gray-700">Event Types (comma-separated) *</label>
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
            <label htmlFor="secret" className="block text-sm font-medium text-gray-700">Secret (Optional)</label>
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

        <div className="mt-6">
          <button
            type="submit"
            disabled={loading}
            className={`w-full md:w-auto px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading ? 'Creating...' : 'Create Subscription'}
          </button>
        </div>
      </form>
    </div>
  );
} 