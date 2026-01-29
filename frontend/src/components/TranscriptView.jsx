import React, { useState } from 'react';
import { MessageSquare, User, Clock } from 'lucide-react';

function TranscriptView({ transcription }) {
  const [expandedSegments, setExpandedSegments] = useState(true);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeakerColor = (speaker) => {
    const colors = {
      'SPEAKER_00': 'bg-blue-100 text-blue-800',
      'SPEAKER_01': 'bg-green-100 text-green-800',
      'SPEAKER_02': 'bg-purple-100 text-purple-800',
      'SPEAKER_03': 'bg-orange-100 text-orange-800',
      'Unknown': 'bg-gray-100 text-gray-800'
    };
    return colors[speaker] || 'bg-pink-100 text-pink-800';
  };

  return (
    <div className="bg-white rounded-xl shadow-xl p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <MessageSquare className="w-8 h-8 text-blue-600" />
          <h2 className="text-3xl font-bold text-gray-800">Full Transcript</h2>
        </div>
        <button
          onClick={() => setExpandedSegments(!expandedSegments)}
          className="text-blue-600 hover:text-blue-700 font-semibold"
        >
          {expandedSegments ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {expandedSegments ? (
        <div className="space-y-4">
          {transcription.segments.map((segment, index) => (
            <div
              key={index}
              className="border-l-4 border-blue-500 pl-4 py-2 hover:bg-gray-50 transition"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getSpeakerColor(segment.speaker)}`}>
                  <User className="w-4 h-4 inline mr-1" />
                  {segment.speaker}
                </span>
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {formatTime(segment.start)} - {formatTime(segment.end)}
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed">{segment.text}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-gray-50 rounded-lg p-6">
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
            {transcription.full_text}
          </p>
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          Language: {transcription.language} | 
          Segments: {transcription.segments.length}
        </p>
      </div>
    </div>
  );
}

export default TranscriptView;
