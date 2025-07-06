import React, { useState } from 'react';
import { User, Settings, Plug } from 'lucide-react';
import ConnectGoogleSheetsButton from '../components/ConnectGoogleSheetsButton';
import { googleSheetsApi } from '../utils/api';
import { useAuth } from '../context/AuthContext';

function UserSettingsPage() {
  const { user } = useAuth();
  const [creating, setCreating] = useState(false);

  const connected = !!user?.google_refresh_token;
  const sheetId = user?.sheets_spreadsheet_id;
  const sheetUrl = sheetId ? `https://docs.google.com/spreadsheets/d/${sheetId}` : null;

  const handleCreateSheet = async () => {
    try {
      setCreating(true);
      const data = await googleSheetsApi.createSheet();
      alert(`Spreadsheet created! ID: ${data.spreadsheet_id}`);
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert('Failed to create sheet');
    } finally {
      setCreating(false);
    }
  };



  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <Settings className="h-6 w-6 text-gray-600" />
        <h1 className="text-3xl font-bold text-gray-900">User Settings</h1>
      </div>

      {/* User Profile Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <User className="h-5 w-5 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-900">Profile Information</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Full Name</label>
            <div className="mt-1 text-sm text-gray-900">
              {user?.full_name || 'Not provided'}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <div className="mt-1 text-sm text-gray-900">
              {user?.email || 'Not provided'}
            </div>
          </div>
        </div>
      </div>

      {/* Integrations Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Plug className="h-5 w-5 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-900">Integrations</h2>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Google Sheets</h3>
            <p className="text-sm text-gray-600 mb-4">
              Connect your Google account to automatically export bills to Google Sheets.
            </p>

            {/* Connect */}
            {!connected && (
              <div className="mb-4">
                <ConnectGoogleSheetsButton onConnected={() => window.location.reload()} />
              </div>
            )}

            {connected && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-green-800">Connected to Google Sheets</span>
                </div>
              </div>
            )}

            {/* Create Sheet */}
            {connected && !sheetId && (
              <div className="mb-4">
                <button
                  onClick={handleCreateSheet}
                  disabled={creating}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md shadow hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {creating ? 'Creating…' : 'Create Expense Sheet'}
                </button>
              </div>
            )}

            {sheetUrl && (
              <div className="mb-4">
                <a
                  href={sheetUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md shadow hover:bg-green-700 transition-colors font-medium"
                >
                  <span>Open Expense Sheet</span>
                  <span>↗</span>
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserSettingsPage; 