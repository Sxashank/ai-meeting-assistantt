import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, TrendingUp } from 'lucide-react';

function MentionTracker({ mentionData }) {
  const [expandedSections, setExpandedSections] = useState({
    transcript: true,
    mentions: false,
    tasks: false,
    stats: false
  });

  if (!mentionData) {
    return null;
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const renderHighlightedTranscript = (transcript) => {
    // Replace [MENTION]text[/MENTION] with highlighted spans
    const parts = transcript.split(/(\[MENTION\][^\[]*\[\/MENTION\])/g);

    return (
      <div className="space-y-2">
        {parts.map((part, idx) => {
          if (part.startsWith('[MENTION]') && part.endsWith('[/MENTION]')) {
            const mentionedText = part.replace('[MENTION]', '').replace('[/MENTION]', '');
            return (
              <span
                key={idx}
                className="bg-yellow-400/30 text-yellow-100 px-2 py-1 rounded font-semibold border border-yellow-500/50"
              >
                {mentionedText}
              </span>
            );
          }
          return <span key={idx}>{part}</span>;
        })}
      </div>
    );
  };

  const getEngagementColor = (level) => {
    switch (level) {
      case 'high':
        return 'from-green-500 to-emerald-500';
      case 'medium':
        return 'from-blue-500 to-cyan-500';
      case 'moderate':
        return 'from-yellow-500 to-orange-500';
      case 'low':
        return 'from-orange-500 to-red-500';
      default:
        return 'from-slate-500 to-slate-600';
    }
  };

  const mentionStats = {
    total: mentionData.mention_count || 0,
    sentences: mentionData.sentence_count || 0,
    tasks: mentionData.assigned_tasks?.length || 0,
    speaker: mentionData.speaker_mentions?.length || 0
  };

  return (
    <div className="space-y-6">
      {/* User Header */}
      <div className="bg-gradient-to-r from-purple-900/30 to-cyan-900/30 rounded-2xl p-6 border border-purple-500/30">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300">
              {mentionData.username}
            </h2>
            <p className="text-purple-300/80 text-sm mt-1">Mention Tracking & Engagement Analysis</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-cyan-300">{mentionStats.total}</div>
            <p className="text-purple-300/80 text-xs">Total Mentions</p>
          </div>
        </div>
      </div>

      {/* Statistics Bar */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Mentions', value: mentionStats.total, icon: '💬' },
          { label: 'Sentences', value: mentionStats.sentences, icon: '📝' },
          { label: 'Tasks', value: mentionStats.tasks, icon: '✓' },
          { label: 'Speaker', value: mentionStats.speaker, icon: '🎤' }
        ].map((stat, idx) => (
          <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-slate-600/30 text-center">
            <div className="text-2xl mb-2">{stat.icon}</div>
            <div className="text-white font-bold text-lg">{stat.value}</div>
            <div className="text-slate-400 text-xs mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Highlighted Transcript Section */}
      <div className="border border-purple-500/30 rounded-2xl overflow-hidden">
        <button
          onClick={() => toggleSection('transcript')}
          className="w-full bg-gradient-to-r from-purple-900/50 to-slate-900/50 hover:from-purple-900/70 hover:to-slate-900/70 px-6 py-4 flex items-center justify-between transition-all"
        >
          <div className="flex items-center gap-3">
            <span className="text-cyan-300">✨</span>
            <span className="font-bold text-white">Highlighted Transcript</span>
          </div>
          {expandedSections.transcript ? (
            <ChevronUp className="w-5 h-5 text-cyan-300" />
          ) : (
            <ChevronDown className="w-5 h-5 text-cyan-300" />
          )}
        </button>

        {expandedSections.transcript && (
          <div className="bg-slate-900/30 p-6 border-t border-purple-500/30">
            <div className="bg-slate-800/50 rounded-lg p-4 text-slate-200 leading-relaxed font-mono text-sm max-h-96 overflow-y-auto">
              {renderHighlightedTranscript(mentionData.highlight_transcript)}
            </div>
          </div>
        )}
      </div>

      {/* Sentences with Mentions */}
      {mentionData.sentences_with_mentions && mentionData.sentences_with_mentions.length > 0 && (
        <div className="border border-cyan-500/30 rounded-2xl overflow-hidden">
          <button
            onClick={() => toggleSection('mentions')}
            className="w-full bg-gradient-to-r from-cyan-900/50 to-slate-900/50 hover:from-cyan-900/70 hover:to-slate-900/70 px-6 py-4 flex items-center justify-between transition-all"
          >
            <div className="flex items-center gap-3">
              <span className="text-yellow-300">📌</span>
              <span className="font-bold text-white">Mentions in Context</span>
              <span className="bg-cyan-500/30 text-cyan-200 px-3 py-1 rounded-full text-xs font-semibold">
                {mentionData.sentences_with_mentions.length}
              </span>
            </div>
            {expandedSections.mentions ? (
              <ChevronUp className="w-5 h-5 text-cyan-300" />
            ) : (
              <ChevronDown className="w-5 h-5 text-cyan-300" />
            )}
          </button>

          {expandedSections.mentions && (
            <div className="bg-slate-900/30 p-6 border-t border-cyan-500/30 space-y-3">
              {mentionData.sentences_with_mentions.map((item, idx) => (
                <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/30">
                  <div className="text-yellow-300 text-xs font-semibold mb-2">
                    Mention #{idx + 1}
                  </div>
                  <p className="text-slate-200 leading-relaxed">{item.sentence}</p>
                  {item.mentions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {item.mentions.map((mention, midx) => (
                        <span key={midx} className="bg-yellow-500/30 text-yellow-200 px-2 py-1 rounded text-xs border border-yellow-500/50">
                          {mention.text}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Assigned Tasks */}
      {mentionData.assigned_tasks && mentionData.assigned_tasks.length > 0 && (
        <div className="border border-green-500/30 rounded-2xl overflow-hidden">
          <button
            onClick={() => toggleSection('tasks')}
            className="w-full bg-gradient-to-r from-green-900/50 to-slate-900/50 hover:from-green-900/70 hover:to-slate-900/70 px-6 py-4 flex items-center justify-between transition-all"
          >
            <div className="flex items-center gap-3">
              <span className="text-green-300">✓</span>
              <span className="font-bold text-white">Assigned Tasks</span>
              <span className="bg-green-500/30 text-green-200 px-3 py-1 rounded-full text-xs font-semibold">
                {mentionData.assigned_tasks.length}
              </span>
            </div>
            {expandedSections.tasks ? (
              <ChevronUp className="w-5 h-5 text-green-300" />
            ) : (
              <ChevronDown className="w-5 h-5 text-green-300" />
            )}
          </button>

          {expandedSections.tasks && (
            <div className="bg-slate-900/30 p-6 border-t border-green-500/30 space-y-3">
              {mentionData.assigned_tasks.map((task, idx) => (
                <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-green-500/30">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-white font-semibold mb-2">{task.task}</p>
                      <p className="text-slate-400 text-sm italic">{task.source_sentence}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold whitespace-nowrap ml-4 ${
                      task.confidence === 'extracted'
                        ? 'bg-green-500/30 text-green-200 border border-green-500/50'
                        : 'bg-blue-500/30 text-blue-200 border border-blue-500/50'
                    }`}>
                      {task.confidence}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Statistics & Engagement */}
      <div className="border border-blue-500/30 rounded-2xl overflow-hidden">
        <button
          onClick={() => toggleSection('stats')}
          className="w-full bg-gradient-to-r from-blue-900/50 to-slate-900/50 hover:from-blue-900/70 hover:to-slate-900/70 px-6 py-4 flex items-center justify-between transition-all"
        >
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-blue-300" />
            <span className="font-bold text-white">Engagement Metrics</span>
          </div>
          {expandedSections.stats ? (
            <ChevronUp className="w-5 h-5 text-blue-300" />
          ) : (
            <ChevronDown className="w-5 h-5 text-blue-300" />
          )}
        </button>

        {expandedSections.stats && (
          <div className="bg-slate-900/30 p-6 border-t border-blue-500/30">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-slate-300 font-semibold">Engagement Level</span>
                  <span className="text-white text-lg font-bold capitalize">
                    {mentionData.username}'s Involvement
                  </span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${getEngagementColor('high')} transition-all`}
                    style={{ width: `${Math.min((mentionStats.total / 20) * 100, 100)}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
                  <p className="text-slate-400 text-xs mb-1">Mention Frequency</p>
                  <p className="text-cyan-300 text-2xl font-bold">{mentionStats.total}</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
                  <p className="text-slate-400 text-xs mb-1">Responsibility</p>
                  <p className="text-green-300 text-2xl font-bold">{mentionStats.tasks}</p>
                </div>
              </div>

              <div className="bg-blue-900/30 rounded-lg p-4 border border-blue-500/30">
                <p className="text-blue-200 text-sm">
                  <strong>{mentionData.username}</strong> was mentioned <strong>{mentionStats.total} times</strong> across <strong>{mentionStats.sentences} sentences</strong> 
                  with <strong>{mentionStats.tasks} task assignments</strong>.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MentionTracker;
