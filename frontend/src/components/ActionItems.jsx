import React from 'react';
import { CheckSquare, User, Calendar, AlertCircle } from 'lucide-react';

function ActionItems({ items }) {
  const getPriorityColor = (priority) => {
    const colors = {
      high: 'bg-red-500/20 text-red-300 border border-red-400/30',
      medium: 'bg-yellow-500/20 text-yellow-300 border border-yellow-400/30',
      low: 'bg-green-500/20 text-green-300 border border-green-400/30'
    };
    return colors[priority] || 'bg-gray-500/20 text-gray-300 border border-gray-400/30';
  };

  const getPriorityIcon = (priority) => {
    if (priority === 'high') {
      return <AlertCircle className="w-4 h-4" />;
    }
    return <CheckSquare className="w-4 h-4" />;
  };

  return (
    <div className="glassmorphism rounded-3xl p-10 border-l-4 border-green-400 slide-up" style={{boxShadow: '0 0 40px rgba(34, 197, 94, 0.2)'}}>
      <div className="flex items-center gap-4 mb-8">
        <CheckSquare className="w-10 h-10 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400" />
        <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">Action Items</h2>
        <span className="bg-gradient-to-r from-green-500/30 to-emerald-500/30 text-green-300 px-4 py-2 rounded-full text-sm font-bold border border-green-400/30">
          {items.length} items
        </span>
      </div>

      <div className="space-y-5">
        {items.map((item, index) => (
          <div
            key={index}
            className="glassmorphism border-2 border-slate-700/50 rounded-2xl p-6 hover:border-green-400/50 smooth-transition hover:shadow-lg hover:shadow-green-400/20"
          >
            <div className="flex items-start justify-between mb-5">
              <h3 className="text-lg font-bold text-white flex-1">
                {item.task}
              </h3>
              <span className={`px-4 py-2 rounded-full text-xs font-bold flex items-center gap-2 flex-shrink-0 ml-4 ${getPriorityColor(item.priority)}`}>
                {getPriorityIcon(item.priority)}
                {item.priority.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="flex items-center gap-3 text-gray-300 bg-slate-800/40 rounded-xl p-3">
                <User className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                <span className="text-sm">
                  <span className="font-bold text-gray-400">Assignee:</span>
                  <span className="text-white block mt-1">{item.assignee}</span>
                </span>
              </div>
              <div className="flex items-center gap-3 text-gray-300 bg-slate-800/40 rounded-xl p-3">
                <Calendar className="w-5 h-5 text-purple-400 flex-shrink-0" />
                <span className="text-sm">
                  <span className="font-bold text-gray-400">Deadline:</span>
                  <span className="text-white block mt-1">{item.deadline}</span>
                </span>
              </div>
            </div>

            <div className="bg-slate-800/40 rounded-xl p-4 border-l-4 border-cyan-400 mb-3">
              <p className="text-sm text-gray-300 italic">
                "{item.context}"
              </p>
            </div>

            <div className="text-right">
              <span className="text-xs text-gray-500 font-semibold">
                Confidence: <span className="text-cyan-400">{(item.confidence * 100).toFixed(0)}%</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ActionItems;
