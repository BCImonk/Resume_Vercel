import { useState } from 'react';

export default function Home() {
  const [resume, setResume] = useState(null);
  const [jd, setJd] = useState(null);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!resume || !jd) {
      alert('Please upload both the resume and job description files.');
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('resume', resume);
    formData.append('jd', jd);

    try {
      const res = await fetch('/api/optimize', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setResult(data.optimized_resume);
    } catch (error) {
      console.error(error);
      setResult('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-gray-800 rounded-lg p-8 shadow-lg transform hover:scale-105 transition-transform duration-300">
        <h1 className="text-2xl font-bold mb-6 text-center">Resume Optimizer</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-1">Upload Resume</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.txt"
              onChange={(e) => setResume(e.target.files[0])}
              className="w-full p-2 bg-gray-700 rounded border border-gray-600"
            />
          </div>
          <div>
            <label className="block mb-1">Upload Job Description</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.txt"
              onChange={(e) => setJd(e.target.files[0])}
              className="w-full p-2 bg-gray-700 rounded border border-gray-600"
            />
          </div>
          <button
            type="submit"
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 rounded font-semibold transition-colors"
          >
            {loading ? 'Optimizing...' : 'Optimize Resume'}
          </button>
        </form>
        {result && (
          <div className="mt-6 p-4 bg-gray-700 rounded">
            <h2 className="text-xl font-semibold mb-2">Optimized Resume</h2>
            <pre className="whitespace-pre-wrap">{result}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
