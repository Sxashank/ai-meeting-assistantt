import React, { useState, useEffect, useRef } from 'react';
import { Mic, FileAudio, Loader2, CheckCircle, Zap } from 'lucide-react';
import AudioUploader from './components/AudioUploader';
import TranscriptView from './components/TranscriptView';
import SummaryPanel from './components/SummaryPanel';
import ActionItems from './components/ActionItems';
import MentionTracker from './components/MentionTracker';
import { uploadMeeting } from './services/api';

function App() {
  const [file, setFile] = useState(null);
  const [userName, setUserName] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState('');
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [cursorStyle, setCursorStyle] = useState({ x: 0, y: 0, scale: 1 });
  const [cursorTrails, setCursorTrails] = useState([]);
  const [hoveredLetters, setHoveredLetters] = useState({});
  const cursorRef = useRef(null);
  const titleRef = useRef(null);
  const trailCounterRef = useRef(0);

  // Enhanced Cursor Physics with Trails
  useEffect(() => {
    let animationFrameId;
    let lastTrailTime = 0;

    const handleMouseMove = (e) => {
      const now = Date.now();
      setMousePos({ x: e.clientX, y: e.clientY });
      
      if (cursorRef.current) {
        cursorRef.current.style.transform = `translate(${e.clientX - 10}px, ${e.clientY - 10}px) scale(${cursorStyle.scale})`;
      }

      // Create trail effect
      if (now - lastTrailTime > 20) {
        setCursorTrails(prev => {
          const newTrails = [...prev, {
            id: trailCounterRef.current++,
            x: e.clientX,
            y: e.clientY,
            opacity: 1
          }];
          return newTrails.slice(-15); // Keep last 15 trails
        });
        lastTrailTime = now;
      }

      // Check if hovering over title letters
      if (titleRef.current) {
        const titleRect = titleRef.current.getBoundingClientRect();
        const relX = e.clientX - titleRect.left;
        const relY = e.clientY - titleRect.top;
        
        const children = titleRef.current.querySelectorAll('span');
        const newHovered = {};
        
        children.forEach((child, idx) => {
          const rect = child.getBoundingClientRect();
          const isHovering = 
            e.clientX >= rect.left && e.clientX <= rect.right &&
            e.clientY >= rect.top && e.clientY <= rect.bottom;
          
          if (isHovering) {
            newHovered[idx] = true;
          }
        });
        
        setHoveredLetters(newHovered);
      }
    };

    const handleMouseDown = () => {
      setCursorStyle(prev => ({ ...prev, scale: 0.5 }));
    };

    const handleMouseUp = () => {
      setCursorStyle(prev => ({ ...prev, scale: 1 }));
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);

    // Fade out trails
    const fadeInterval = setInterval(() => {
      setCursorTrails(prev => prev.map(trail => ({
        ...trail,
        opacity: trail.opacity - 0.08
      })).filter(trail => trail.opacity > 0));
    }, 30);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      clearInterval(fadeInterval);
    };
  }, [cursorStyle.scale]);

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setError(null);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setProcessing(true);
    setError(null);
    setProgress('Uploading audio file...');

    try {
      setProgress('Transcribing audio...');
      const data = await uploadMeeting(file, userName, (progressMsg) => {
        setProgress(progressMsg);
      });
      
      setResult(data);
      setProgress('Complete!');
    } catch (err) {
      setError(err.message || 'An error occurred during processing');
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen overflow-hidden relative cursor-none" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1a1a3e 50%, #0f0f2e 100%)' }}>
      {/* Cursor Trails */}
      {cursorTrails.map((trail) => (
        <div
          key={trail.id}
          className="fixed w-3 h-3 bg-gradient-to-r from-cyan-400 to-purple-400 rounded-full pointer-events-none z-40"
          style={{
            left: `${trail.x - 6}px`,
            top: `${trail.y - 6}px`,
            opacity: trail.opacity * 0.6,
            boxShadow: `0 0 10px rgba(34, 211, 238, ${trail.opacity * 0.8})`
          }}
        />
      ))}

      {/* Custom Main Cursor */}
      <div
        ref={cursorRef}
        className="fixed w-5 h-5 pointer-events-none z-50 transition-transform"
        style={{
          background: 'radial-gradient(circle, #00ffff 0%, #a855f7 100%)',
          borderRadius: '50%',
          boxShadow: `0 0 15px rgba(34, 211, 238, 1), 0 0 30px rgba(168, 85, 247, 0.8), 0 0 50px rgba(6, 182, 212, 0.6)`,
          transform: `scale(${cursorStyle.scale})`,
          transition: 'all 0.1s ease-out'
        }}
      />

      {/* Cursor Outer Ring */}
      <div
        className="fixed w-8 h-8 border-2 border-cyan-400 rounded-full pointer-events-none z-40"
        style={{
          left: `${mousePos.x - 16}px`,
          top: `${mousePos.y - 16}px`,
          opacity: 0.5,
          boxShadow: '0 0 20px rgba(6, 182, 212, 0.5)',
          transition: 'all 0.15s ease-out'
        }}
      />

      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-purple-600 to-transparent rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute top-40 right-10 w-96 h-96 bg-gradient-to-bl from-blue-600 to-transparent rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute -bottom-20 left-32 w-96 h-96 bg-gradient-to-tr from-cyan-500 to-transparent rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '4s' }} />
        <div className="absolute bottom-40 right-32 w-80 h-80 bg-gradient-to-tl from-pink-500 to-transparent rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="container mx-auto px-4 py-12 relative z-10">
        {/* Premium Header */}
        <div className="text-center mb-16 slide-up">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="relative">
              <Mic className="w-16 h-16 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400 float-animation" />
            </div>
            <div className="relative group cursor-pointer" ref={titleRef}>
              <div className="text-7xl font-black leading-tight">
                {'AI Meeting Assistant'.split('').map((letter, idx) => (
                  <span
                    key={idx}
                    className={`inline-block transition-all duration-200 ${
                      hoveredLetters[idx] 
                        ? 'scale-125 text-yellow-300 drop-shadow-lg' 
                        : 'text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400'
                    }`}
                    style={{
                      textShadow: hoveredLetters[idx] 
                        ? '0 0 20px rgba(253, 224, 71, 0.8), 0 0 40px rgba(59, 130, 246, 0.6)' 
                        : 'none',
                      filter: hoveredLetters[idx] 
                        ? 'drop-shadow(0 0 10px #ffd700) drop-shadow(0 0 20px #00ffff)' 
                        : 'none'
                    }}
                  >
                    {letter === ' ' ? '\u00A0' : letter}
                  </span>
                ))}
              </div>
              {/* Hover glow effect */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10" style={{
                background: 'linear-gradient(to right, #00ffff, #ff00ff, #ffff00)',
                filter: 'blur(20px)',
                borderRadius: '50%'
              }} />
            </div>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
            <span className="inline-flex items-center gap-2 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 font-semibold">
              <Zap className="w-5 h-5" /> Powered by AI
            </span>
            <br />Automatic transcription, speaker identification, summarization, and action items
          </p>
        </div>

        {/* Upload Section */}
        {!result && (
          <div className="max-w-3xl mx-auto">
            <AudioUploader
              onFileSelect={handleFileSelect}
              selectedFile={file}
              processing={processing}
              onUpload={handleUpload}
              userName={userName}
              onUserNameChange={setUserName}
            />
            
            {processing && (
              <div className="mt-8 glassmorphism rounded-2xl p-8 glow-effect">
                <div className="flex items-center gap-4 mb-6">
                  <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                  <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
                    {progress}
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                  <div className="bg-gradient-to-r from-cyan-400 to-purple-500 h-3 rounded-full animate-pulse w-2/3 shadow-lg shadow-cyan-400/50"></div>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-8 glassmorphism border-l-4 border-red-500 rounded-2xl p-6 bg-red-500/10">
                <p className="text-red-300 font-semibold text-lg">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* Results Section */}
        {result && !processing && (
          <div className="space-y-6">
            {/* Success Banner */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <div>
                <p className="font-bold text-green-300 text-lg">Processing Complete!</p>
                <p className="text-sm text-green-400/80">
                  Meeting: {result.filename} ({result.duration}s)
                </p>
              </div>
            </div>

            {/* Summary Panel */}
            <SummaryPanel summary={result.summary} />

            {/* Mention Tracker (if available) */}
            {result.mention_tracking && (
              <MentionTracker mentionData={result.mention_tracking} />
            )}

            {/* Action Items */}
            <ActionItems items={result.action_items} />

            {/* Transcript */}
            <TranscriptView transcription={result.transcription} />

            {/* New Upload Button */}
            <div className="text-center pt-4">
              <button
                onClick={() => {
                  setResult(null);
                  setFile(null);
                }}
                className="bg-gradient-to-r from-cyan-500 to-purple-500 text-white px-10 py-4 rounded-xl font-bold hover:shadow-lg hover:shadow-purple-500/50 smooth-transition hover:scale-105"
              >
                Process Another Meeting
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;