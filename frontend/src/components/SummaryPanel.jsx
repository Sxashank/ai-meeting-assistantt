import React from 'react';
import { FileText, TrendingUp } from 'lucide-react';

function SummaryPanel({ summary }) {
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-xl p-8 border border-purple-200">
      <div className="flex items-center gap-3 mb-6">
        <FileText className="w-8 h-8 text-purple-600" />
        <h2 className="text-3xl font-bold text-gray-800">Meeting Summary</h2>
      </div>

      <div className="bg-white rounded-lg p-6 mb-6">
        <p className="text-lg text-gray-700 leading-relaxed">
          {summary.summary}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 mb-1">Original Length</p>
          <p className="text-2xl font-bold text-gray-800">
            {summary.original_length}
            <span className="text-sm font-normal text-gray-500 ml-1">chars</span>
          </p>
        </div>
        <div className="bg-white rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 mb-1">Summary Length</p>
          <p className="text-2xl font-bold text-gray-800">
            {summary.summary_length}
            <span className="text-sm font-normal text-gray-500 ml-1">chars</span>
          </p>
        </div>
        <div className="bg-white rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 mb-1 flex items-center justify-center gap-1">
            <TrendingUp className="w-4 h-4" />
            Compression
          </p>
          <p className="text-2xl font-bold text-green-600">
            {summary.compression_ratio}x
          </p>
        </div>
      </div>
    </div>
  );
}

export default SummaryPanel;
