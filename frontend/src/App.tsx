import { useState } from 'react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file');
      return;
    }

    setLoading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      setMessage(`✅ Upload successful! Document ID: ${data.document_id}`);
    } catch (error) {
      setMessage('❌ Upload failed. Make sure the backend is running on port 8000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            📚 RAG Document QA
          </h1>
          <p className="text-gray-500">
            Upload a document and ask questions
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Document (PDF, DOCX, or TXT)
          </label>
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {file && (
            <p className="mt-2 text-sm text-green-600">
              Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className={`w-full py-2 px-4 rounded-lg font-medium transition-all duration-200
            ${!file || loading 
              ? 'bg-gray-300 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg'
            }`}
        >
          {loading ? 'Uploading...' : 'Upload Document'}
        </button>

        {message && (
          <div className={`mt-4 p-3 rounded-lg text-sm ${
            message.startsWith('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {message}
          </div>
        )}

        <div className="mt-6 pt-4 border-t text-center text-xs text-gray-400">
          Backend: {API_BASE} | FastAPI + LangChain
        </div>
      </div>
    </div>
  );
}

export default App;