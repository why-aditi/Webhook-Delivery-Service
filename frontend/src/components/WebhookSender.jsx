import { useState } from 'react';
import api from '../utils/api';

export default function WebhookSender({ subscriptionId }) {
  const [formData, setFormData] = useState({
    event_type: '',
    data: {}
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await api.post(`/ingest/${subscriptionId}`, {
        event_type: formData.event_type,
        data: formData.data
      });

      setSuccess(true);
      setFormData({ event_type: '', data: {} });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send webhook');
      console.error('Error sending webhook:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleDataChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      data: {
        ...prev.data,
        [name]: value
      }
    }));
  };

  return (
    <div className="w-full bg-white rounded-lg shadow">
      <form onSubmit={handleSubmit} className="p-6 sm:p-8">
        <h2 className="text-2xl font-semibold mb-6 text-gray-900">Send Webhook</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="event_type" className="block text-sm font-medium text-gray-700">Event Type *</label>
            <input
              type="text"
              id="event_type"
              name="event_type"
              required
              value={formData.event_type}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 placeholder-gray-400"
              placeholder="Enter event type"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Data</label>
            <div className="mt-1 space-y-2">
              <input
                type="text"
                name="key1"
                value={formData.data.key1 || ''}
                onChange={handleDataChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 placeholder-gray-400"
                placeholder="Key"
              />
              <input
                type="text"
                name="value1"
                value={formData.data.value1 || ''}
                onChange={handleDataChange}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-gray-900 placeholder-gray-400"
                placeholder="Value"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 text-red-500 text-sm">{error}</div>
        )}

        {success && (
          <div className="mt-4 text-green-500 text-sm">Webhook sent successfully!</div>
        )}

        <div className="mt-6">
          <button
            type="submit"
            disabled={loading}
            className={`w-full md:w-auto px-6 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading ? 'Sending...' : 'Send Webhook'}
          </button>
        </div>
      </form>
    </div>
  );
} 