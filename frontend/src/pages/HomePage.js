import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, Camera, FileText, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import axios from 'axios';

function HomePage() {
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [billData, setBillData] = useState(null);
  const navigate = useNavigate();

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/v1/bills/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        params: {
          downsize: false
        }
      });

      setBillData(response.data);
      setSuccess(true);
      setTimeout(() => {
        navigate(`/bills/${response.data.id}`);
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process bill. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    },
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Digitize Your Bills Instantly
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Upload a photo of your receipt or bill and get structured data in seconds
        </p>
      </div>

      {/* Upload Area */}
      <div className="mb-8">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : uploading
              ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-primary-500 hover:bg-primary-50'
          }`}
        >
          <input {...getInputProps()} />
          
          {uploading ? (
            <div className="flex flex-col items-center">
              <Loader className="h-12 w-12 text-primary-600 animate-spin mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">Processing your bill...</p>
              <p className="text-gray-600">This may take a few moments</p>
            </div>
          ) : success ? (
            <div className="flex flex-col items-center">
              <CheckCircle className="h-12 w-12 text-green-600 mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">Bill processed successfully!</p>
              <p className="text-gray-600">Redirecting to bill details...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center">
              <AlertCircle className="h-12 w-12 text-red-600 mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">Processing failed</p>
              <p className="text-red-600 mb-4">{error}</p>
              <p className="text-gray-600">Click or drag to try again</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <Upload className="h-12 w-12 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop your bill here' : 'Upload a bill or receipt'}
              </p>
              <p className="text-gray-600 mb-4">
                Drag and drop an image, or click to select a file
              </p>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span className="flex items-center">
                  <Camera className="h-4 w-4 mr-1" />
                  Photos
                </span>
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  PNG, JPG, JPEG
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="text-center p-6 bg-white rounded-lg shadow-sm">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Camera className="h-6 w-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Recognition</h3>
          <p className="text-gray-600">
            AI-powered text extraction from receipts, bills, and invoices
          </p>
        </div>

        <div className="text-center p-6 bg-white rounded-lg shadow-sm">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <FileText className="h-6 w-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Structured Data</h3>
          <p className="text-gray-600">
            Get organized data including items, prices, taxes, and merchant info
          </p>
        </div>

        <div className="text-center p-6 bg-white rounded-lg shadow-sm">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-6 w-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Instant Results</h3>
          <p className="text-gray-600">
            Fast processing with detailed breakdown of all bill components
          </p>
        </div>
      </div>
    </div>
  );
}

export default HomePage; 