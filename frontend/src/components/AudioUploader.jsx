import React, { useRef, useState } from 'react';
import { Upload, FileAudio, X } from 'lucide-react';

function AudioUploader({ onFileSelect, selectedFile, processing, onUpload, userName, onUserNameChange }) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="relative group">
      {/* Glowing border effect */}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 rounded-3xl opacity-30 group-hover:opacity-100 blur transition duration-500" />
      
      {/* Main container */}
      <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-black rounded-3xl p-1">
        {/* Inner content */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl p-10">
          {!selectedFile ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all duration-300 ${
                isDragging
                  ? 'border-cyan-400 bg-cyan-500/10'
                  : 'border-slate-600 hover:border-purple-400 hover:bg-purple-500/5'
              }`}
            >
              <Upload className={`w-20 h-20 mx-auto mb-6 transition-all duration-300 ${
                isDragging ? 'text-cyan-400 scale-110' : 'text-purple-300'
              }`} />
              <p className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-300 to-purple-300 mb-2">
                Drop your audio file here
              </p>
              <p className="text-purple-300/80 mb-4 text-lg font-semibold">
                or click to browse
              </p>
              <p className="text-sm text-slate-400 font-medium">
                <span className="text-cyan-300">Supported:</span> WAV, MP3, M4A, FLAC, OGG (Max 100MB)
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".wav,.mp3,.m4a,.flac,.ogg"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          ) : (
            <div>
              <div className="mb-6">
                <label className="block text-sm font-semibold text-purple-300 mb-3">
                  Your Name (Optional - for personalized insights)
                </label>
                <input
                  type="text"
                  value={userName}
                  onChange={(e) => onUserNameChange(e.target.value)}
                  placeholder="e.g., Shashank"
                  className="w-full px-4 py-3 rounded-xl bg-slate-700/50 border border-purple-500/30 text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30 transition-all duration-300"
                />
              </div>
              <div className="flex items-center justify-between bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-2xl p-6 mb-6 border border-purple-500/30">
                <div className="flex items-center gap-4">
                  <FileAudio className="w-10 h-10 text-cyan-400" />
                  <div>
                    <p className="font-bold text-white text-lg">{selectedFile.name}</p>
                    <p className="text-purple-300/80 text-sm font-semibold">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                {!processing && (
                  <button
                    onClick={() => onFileSelect(null)}
                    className="text-slate-400 hover:text-red-400 transition-colors smooth-transition"
                  >
                    <X className="w-6 h-6" />
                  </button>
                )}
              </div>

              <button
                onClick={onUpload}
                disabled={processing}
                className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-300 smooth-transition ${
                  processing
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white hover:shadow-lg hover:shadow-purple-500/50 hover:scale-105'
                }`}
              >
                {processing ? 'Processing...' : 'Process Meeting'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AudioUploader;