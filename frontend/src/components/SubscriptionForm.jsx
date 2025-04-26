import { useState } from 'react';
import axios from 'axios';

export default function SubscriptionForm({ onSubscriptionAdded }) {
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    headers: '',
    events: ''
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Parse headers from JSON string to object
      const headers = formData.headers ? JSON.parse(formData.headers) : {};
      // Split events into array
      const events = formData.events.split(',').map(event => event.trim()).filter(Boolean);

      const response = await axios.post('/api/subscriptions', {
        name: formData.name,
        url: formData.url,
        headers,
        events
      });

      setFormData({ name: '', url: '', headers: '', events: '' });
      onSubscriptionAdded(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create subscription');
      console.error('Error creating subscription:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Add New Subscription</h2>
      
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name (Optional)</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder="Subscription name"
        />
      </div>

      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700">Webhook URL *</label>
        <input
          type="url"
          id="url"
          name="url"
          required
          value={formData.url}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder="https://example.com/webhook"
        />
      </div>

      <div>
        <label htmlFor="events" className="block text-sm font-medium text-gray-700">Events (comma-separated) *</label>
        <input
          type="text"
          id="events"
          name="events"
          required
          value={formData.events}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder="event1,event2,event3"
        />
      </div>

      <div>
        <label htmlFor="headers" className="block text-sm font-medium text-gray-700">Headers (JSON format)</label>
        <textarea
          id="headers"
          name="headers"
          value={formData.headers}
          onChange={handleChange}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder='{"Authorization": "Bearer token"}'
        />
      </div>

      {error && (
        <div className="text-red-500 text-sm">{error}</div>
      )}

      <button
        type="submit"
        disabled={loading}
        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
          loading ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        {loading ? 'Creating...' : 'Create Subscription'}
      </button>
    </form>
  );
} 