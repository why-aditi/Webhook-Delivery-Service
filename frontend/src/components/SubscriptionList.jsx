import { useState, useEffect } from 'react';
import { TrashIcon, PencilIcon, EyeIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import EditSubscriptionForm from './EditSubscriptionForm';
import api from '../utils/api';

export default function SubscriptionList() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [deliveryStatus, setDeliveryStatus] = useState(null);
  const [expandedSubscriptions, setExpandedSubscriptions] = useState(new Set());
  const [logs, setLogs] = useState({});

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/subscriptions/');
      console.log('Subscriptions response:', response.data);
      setSubscriptions(response.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch subscriptions');
      console.error('Error fetching subscriptions:', err);
      setSubscriptions([]);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchLogs = async (subscriptionId) => {
    try {
      const response = await api.get(`/subscriptions/${subscriptionId}/deliveries`);
      console.log('Logs response:', response.data);
      setLogs(prev => ({
        ...prev,
        [subscriptionId]: response.data?.recent_deliveries || []
      }));
    } catch (err) {
      console.error('Error fetching logs:', err);
      setLogs(prev => ({
        ...prev,
        [subscriptionId]: []
      }));
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  const toggleSubscription = (subscriptionId) => {
    setExpandedSubscriptions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(subscriptionId)) {
        newSet.delete(subscriptionId);
      } else {
        newSet.add(subscriptionId);
        if (!logs[subscriptionId]) {
          fetchLogs(subscriptionId);
        }
      }
      return newSet;
    });
  };

  const deleteSubscription = async (id) => {
    if (!window.confirm('Are you sure you want to delete this subscription?')) {
      return;
    }

    try {
      await api.delete(`/api/subscriptions/${id}`);
      setSubscriptions(subscriptions.filter(sub => sub.id !== id));
    } catch (err) {
      setError('Failed to delete subscription');
      console.error('Error deleting subscription:', err);
    }
  };

  const handleEdit = (subscription) => {
    setEditingSubscription(subscription);
  };

  const handleUpdateSuccess = (updatedSubscription) => {
    setSubscriptions(subscriptions.map(sub => 
      sub.id === updatedSubscription.id ? updatedSubscription : sub
    ));
    setEditingSubscription(null);
  };

  const fetchDeliveryStatus = async (deliveryId) => {
    try {
      const response = await api.get(`/deliveries/${deliveryId}`);
      setDeliveryStatus(response.data);
    } catch (err) {
      console.error('Error fetching delivery status:', err);
      setError('Failed to fetch delivery status');
    }
  };

  if (loading) return <div className="h-full w-full flex items-center justify-center">Loading...</div>;
  if (error) return <div className="h-full w-full flex items-center justify-center text-red-500">{error}</div>;

  if (editingSubscription) {
    return (
      <EditSubscriptionForm
        subscriptionId={editingSubscription.id}
        onSubscriptionUpdated={handleUpdateSuccess}
        onCancel={() => setEditingSubscription(null)}
      />
    );
  }

  return (
    <div className="h-full w-80vh flex flex-col">
      <h2 className="text-2xl font-semibold mb-4 flex-none">Webhook Subscriptions</h2>
      <div className="flex-1 w-full bg-white shadow rounded-lg divide-y overflow-auto">
        {subscriptions.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500">No subscriptions found</p>
          </div>
        ) : (
          subscriptions.map((subscription) => (
            <div key={subscription.id} className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-grow">
                  <h3 className="font-medium text-black">Target URL: {subscription.target_url}</h3>
                  <p className="text-sm text-gray-500">
                    Event Types: {Array.isArray(subscription.event_types) 
                      ? subscription.event_types.join(', ') 
                      : subscription.event_types}
                  </p>
                </div>
                <div className="flex space-x-4 ml-4">
                  <button
                    onClick={() => toggleSubscription(subscription.id)}
                    className="p-2 bg-white rounded-full text-black hover:bg-gray-100"
                    title="View Logs"
                  >
                    {expandedSubscriptions.has(subscription.id) ? (
                      <ChevronUpIcon className="h-5 w-5" />
                    ) : (
                      <ChevronDownIcon className="h-5 w-5" />
                    )}
                  </button>
                  <button
                    onClick={() => handleEdit(subscription)}
                    className="p-2 bg-white rounded-full text-black hover:bg-gray-100"
                    title="Edit Subscription"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => deleteSubscription(subscription.id)}
                    className="p-2 bg-white rounded-full text-black hover:bg-gray-100"
                    title="Delete Subscription"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Delivery Logs Section */}
              {expandedSubscriptions.has(subscription.id) && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Delivery Logs</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    {logs[subscription.id]?.length > 0 ? (
                      <div className="space-y-2">
                        {logs[subscription.id].map((log) => (
                          <div
                            key={log.id}
                            className="flex items-center justify-between p-2 bg-white rounded-md shadow-sm"
                          >
                            <div>
                              <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                                log.status === 'delivered' 
                                  ? 'bg-green-100 text-green-800' 
                                  : log.status === 'failed'
                                  ? 'bg-red-100 text-red-800'
                                  : log.status === 'in_progress'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {log.status === 'delivered' ? 'Delivered' : log.status}
                              </span>
                              <span className="ml-2 text-sm text-gray-600">
                                {new Date(log.created_at).toLocaleString()}
                              </span>
                            </div>
                            <button
                              onClick={() => {
                                setSelectedDelivery(log);
                                fetchDeliveryStatus(log.id);
                              }}
                              className="text-sm bg-blue-600 text-white"
                            >
                              View Details
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 text-center">No delivery logs found</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Delivery Status Modal */}
      {selectedDelivery && deliveryStatus && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-black">Delivery Details</h3>
              <button
                onClick={() => {
                  setSelectedDelivery(null);
                  setDeliveryStatus(null);
                }}
                className="text-gray-400 hover:text-gray-500"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700">Status</h4>
                <p className={`mt-1 ${
                  deliveryStatus.status === 'delivered' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {deliveryStatus.status}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700">Event Type</h4>
                <p className="mt-1  text-black">{deliveryStatus.event_type}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700">Created At</h4>
                <p className="mt-1 text-black">{new Date(deliveryStatus.created_at).toLocaleString()}</p>
              </div>
              {deliveryStatus.response_code && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Response Code</h4>
                  <p className="mt-1">{deliveryStatus.response_code}</p>
                </div>
              )}
              {deliveryStatus.error && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Error</h4>
                  <p className="mt-1 text-red-600">{deliveryStatus.error}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 