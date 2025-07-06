import React, { useEffect, useState } from 'react';
import ConnectGoogleSheetsButton from '../components/ConnectGoogleSheetsButton';
import { googleSheetsApi } from '../utils/api';
import { useAuth } from '../context/AuthContext';

function IntegrationsPage() {
  const { user } = useAuth();
  const [creating, setCreating] = useState(false);
  const [autoExport, setAutoExport] = useState(user?.auto_export_to_sheets || false);

  const connected = !!user?.google_refresh_token;
  const sheetId = user?.sheets_spreadsheet_id;
  const sheetUrl = sheetId ? `https://docs.google.com/spreadsheets/d/${sheetId}` : null;

  useEffect(() => {
    setAutoExport(user?.auto_export_to_sheets || false);
  }, [user]);

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

  const handleToggleChange = async (e) => {
    const newValue = e.target.checked;
    setAutoExport(newValue);
    try {
      await googleSheetsApi.updateSettings(newValue);
    } catch (err) {
      console.error(err);
      alert('Failed to update setting');
      setAutoExport(!newValue); // revert
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold mb-4">Google Sheets Integration</h2>

      {/* Connect */}
      {!connected && (
        <ConnectGoogleSheetsButton onConnected={() => window.location.reload()} />
      )}

      {/* Create Sheet */}
      {!sheetId && (
        <div>
          <button
            onClick={handleCreateSheet}
            disabled={creating || !connected}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md shadow disabled:opacity-50"
          >
            {creating ? 'Creating…' : 'Create Expense Sheet'}
          </button>
        </div>
      )}

      {sheetUrl && (
        <div className="mt-2">
          <a
            href={sheetUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 underline"
          >
            Open Expense Sheet ↗
          </a>
        </div>
      )}

      {/* Auto-export toggle */}
      <div className="flex items-center space-x-3 mt-6">
        <input
          type="checkbox"
          id="autoExport"
          checked={autoExport}
          onChange={handleToggleChange}
          disabled={!connected}
          className="h-4 w-4 disabled:opacity-50"
        />
        <label htmlFor="autoExport" className="text-sm text-gray-700">
          Automatically export new bills to Google Sheets after review
        </label>
      </div>
    </div>
  );
}

export default IntegrationsPage; 