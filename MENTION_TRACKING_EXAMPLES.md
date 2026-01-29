# Mention Tracking - Code Examples & Advanced Usage

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Advanced Features](#advanced-features)
3. [Custom Implementations](#custom-implementations)
4. [Frontend Integration](#frontend-integration)
5. [Testing Patterns](#testing-patterns)
6. [Performance Optimization](#performance-optimization)

---

## Basic Usage

### Example 1: Simple Upload with Tracking

```bash
# Upload meeting with username
curl -X POST http://localhost:8000/api/v1/meetings/upload \
  -F "file=@team_meeting.wav" \
  -F "user_name=Shashank"

# Response includes mention_tracking with user mentions
```

### Example 2: Python Requests

```python
import requests

# Upload file
response = requests.post(
    "http://localhost:8000/api/v1/meetings/upload",
    files={"file": open("meeting.wav", "rb")},
    params={"user_name": "Shashank"}
)

# Get mention data
data = response.json()
mentions = data.get("mention_tracking", {})

# Display results
print(f"Username: {mentions['username']}")
print(f"Total Mentions: {mentions['mention_count']}")
print(f"Sentences: {len(mentions['sentences_with_mentions'])}")
print(f"Tasks: {len(mentions['assigned_tasks'])}")
```

### Example 3: JavaScript/Fetch

```javascript
// Upload with user_name parameter
const formData = new FormData();
formData.append('file', audioFile);

const response = await fetch(
  'http://localhost:8000/api/v1/meetings/upload?user_name=Shashank',
  {
    method: 'POST',
    body: formData
  }
);

const result = await response.json();
const mentions = result.mention_tracking;

console.log(`Found ${mentions.mention_count} mentions`);
```

---

## Advanced Features

### Feature 1: Working with Highlighted Transcript

```python
# The highlight_transcript contains [MENTION] tags
transcript = mentions['highlight_transcript']

# Parse and extract just mentions
import re
mention_pattern = r'\[MENTION\](.*?)\[/MENTION\]'
found_mentions = re.findall(mention_pattern, transcript)

print("All mentioned texts:")
for mention in found_mentions:
    print(f"  - {mention}")

# Output:
# All mentioned texts:
#   - Shashank
#   - Shashank
#   - Shashank Kumar
```

### Feature 2: Processing Sentences with Mentions

```python
# Each sentence with mentions includes position data
for sentence_info in mentions['sentences_with_mentions']:
    sentence = sentence_info['sentence']
    mention_count = sentence_info['mention_count']
    mentions_in_sentence = sentence_info['mentions']
    
    print(f"\nSentence: {sentence}")
    print(f"Mentions in this sentence: {mention_count}")
    for mention in mentions_in_sentence:
        print(f"  - '{mention['text']}' at position {mention['position_in_sentence']}")
```

### Feature 3: Task Assignment Analysis

```python
# Analyze assigned tasks
for task in mentions['assigned_tasks']:
    print(f"\nTask: {task['task']}")
    print(f"Assigned to: {task['assigned_to']}")
    print(f"Context: {task['source_sentence']}")
    print(f"Confidence: {task['confidence']}")

# Create task list for project management
tasks_list = [
    {
        "title": task['task'],
        "assignee": task['assigned_to'],
        "status": "pending",
        "extracted_from_meeting": True
    }
    for task in mentions['assigned_tasks']
]

# Save to JSON
import json
with open('extracted_tasks.json', 'w') as f:
    json.dump(tasks_list, f, indent=2)
```

### Feature 4: Engagement Analysis

```python
# Analyze engagement level
def analyze_engagement(mentions):
    mention_count = mentions['mention_count']
    sentence_count = mentions['sentence_count']
    task_count = len(mentions['assigned_tasks'])
    
    engagement = {
        "mention_frequency": mention_count,
        "average_mentions_per_sentence": mention_count / sentence_count if sentence_count > 0 else 0,
        "responsibility_level": task_count,
        "engagement_type": classify_engagement(mention_count),
        "insights": generate_insights(mentions)
    }
    
    return engagement

def classify_engagement(count):
    if count >= 20: return "Very Active"
    elif count >= 10: return "Active"
    elif count >= 5: return "Moderately Active"
    elif count > 0: return "Mentioned"
    else: return "Not Mentioned"

def generate_insights(mentions):
    insights = []
    
    if mentions['mention_count'] >= 15:
        insights.append("User was central to the discussion")
    
    if len(mentions['assigned_tasks']) >= 3:
        insights.append("User has significant responsibilities")
    
    if mentions['speaker_mentions']:
        insights.append("User participated as a speaker")
    
    return insights

# Usage
engagement = analyze_engagement(mentions)
print(f"Engagement: {engagement['engagement_type']}")
for insight in engagement['insights']:
    print(f"  • {insight}")
```

---

## Custom Implementations

### Implementation 1: Custom Task Pattern

```python
# In mention_tracker.py, customize task_patterns

# Add pattern for "TODO" items
def extract_personal_todos(self, sentences, username, name_variations):
    todos = []
    
    # Look for TODO mentions
    for sentence_dict in sentences:
        sentence = sentence_dict['sentence'].upper()
        
        if 'TODO' in sentence and any(var in sentence for var in name_variations):
            # Extract TODO content
            match = re.search(r'TODO[:\s]+(.+?)(?:[.!?]|$)', sentence)
            if match:
                todo = {
                    "item": match.group(1).strip(),
                    "type": "todo",
                    "assigned_to": username,
                    "source": sentence_dict['sentence']
                }
                todos.append(todo)
    
    return todos
```

### Implementation 2: Mention Timeline

```python
# Build timeline of when user was mentioned
def get_mention_timeline(transcript, mentions, segments):
    """Build timeline of mentions with timestamps"""
    
    timeline = []
    
    for mention in mentions:
        position = mention['position']
        
        # Find which segment this position falls in
        for segment in segments:
            segment_start = len(segment.get('text', '')) * segment.get('start', 0) / 1000
            if position < segment_start + len(segment.get('text', '')):
                timeline.append({
                    "time": segment.get('start', 0),
                    "text": mention['matched_text'],
                    "context": mention['context'],
                    "speaker": segment.get('speaker', 'Unknown')
                })
                break
    
    return sorted(timeline, key=lambda x: x['time'])
```

### Implementation 3: Export to CSV

```python
import csv
from datetime import datetime

def export_mention_tracking_to_csv(mentions, output_file='mentions.csv'):
    """Export mention tracking data to CSV"""
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Username',
            'Total Mentions',
            'Sentences',
            'Tasks',
            'Engagement Level',
            'Export Date'
        ])
        
        # Main data
        writer.writerow([
            mentions['username'],
            mentions['mention_count'],
            len(mentions['sentences_with_mentions']),
            len(mentions['assigned_tasks']),
            get_engagement_level(mentions['mention_count']),
            datetime.now().isoformat()
        ])
        
        # Sentences sheet
        writer.writerow([])
        writer.writerow(['Sentences with Mentions'])
        writer.writerow(['Sentence', 'Mention Count'])
        
        for sentence in mentions['sentences_with_mentions']:
            writer.writerow([
                sentence['sentence'],
                sentence['mention_count']
            ])
        
        # Tasks sheet
        writer.writerow([])
        writer.writerow(['Assigned Tasks'])
        writer.writerow(['Task', 'Assigned To', 'Confidence'])
        
        for task in mentions['assigned_tasks']:
            writer.writerow([
                task['task'],
                task['assigned_to'],
                task['confidence']
            ])
    
    print(f"Exported to {output_file}")

# Usage
export_mention_tracking_to_csv(mentions)
```

### Implementation 4: Generate Report

```python
def generate_mention_report(mentions, user_profile=None):
    """Generate professional report from mention tracking"""
    
    report = f"""
    {'='*60}
    MEETING PARTICIPATION REPORT
    {'='*60}
    
    USER INFORMATION
    {'-'*60}
    Name: {mentions['username']}
    Report Generated: {mentions['tracked_at']}
    
    PARTICIPATION SUMMARY
    {'-'*60}
    Total Mentions: {mentions['mention_count']}
    Sentences Mentioned: {len(mentions['sentences_with_mentions'])}
    Tasks Assigned: {len(mentions['assigned_tasks'])}
    
    ENGAGEMENT ASSESSMENT
    {'-'*60}
    """
    
    engagement = get_engagement_level(mentions['mention_count'])
    report += f"    Engagement Level: {engagement}\n"
    
    if mentions['assigned_tasks']:
        report += f"\n    ASSIGNED TASKS\n    {'-'*60}\n"
        for i, task in enumerate(mentions['assigned_tasks'], 1):
            report += f"    {i}. {task['task']}\n"
            report += f"       From: {task['source_sentence']}\n\n"
    
    report += f"\n    {'='*60}\n"
    
    return report

# Usage
report = generate_mention_report(mentions)
print(report)

# Save report
with open('mention_report.txt', 'w') as f:
    f.write(report)
```

---

## Frontend Integration

### Integration 1: React Custom Hook

```jsx
// hooks/useMentionTracking.js
import { useState, useEffect } from 'react';

export function useMentionTracking(mentionData) {
  const [expanded, setExpanded] = useState({
    transcript: true,
    mentions: false,
    tasks: false,
    stats: false
  });
  
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    if (mentionData) {
      setStats({
        totalMentions: mentionData.mention_count,
        sentences: mentionData.sentence_count,
        tasks: mentionData.assigned_tasks?.length || 0,
        speakers: mentionData.speaker_mentions?.length || 0
      });
    }
  }, [mentionData]);
  
  const toggleSection = (section) => {
    setExpanded(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };
  
  return {
    expanded,
    toggleSection,
    stats,
    hasData: !!mentionData
  };
}

// Usage in component
function MentionTrackerCustom({ mentionData }) {
  const { expanded, toggleSection, stats } = useMentionTracking(mentionData);
  
  return (
    <div>
      <h2>{mentionData.username} - {stats.totalMentions} Mentions</h2>
      {/* Render using state */}
    </div>
  );
}
```

### Integration 2: Export Button Component

```jsx
function ExportMentionData({ mentionData }) {
  const handleExportJSON = () => {
    const json = JSON.stringify(mentionData, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${mentionData.username}-mentions.json`;
    a.click();
  };
  
  const handleExportCSV = () => {
    let csv = 'Metric,Value\n';
    csv += `Total Mentions,${mentionData.mention_count}\n`;
    csv += `Sentences,${mentionData.sentence_count}\n`;
    csv += `Tasks,${mentionData.assigned_tasks?.length || 0}\n`;
    
    csv += '\nSentences\n';
    mentionData.sentences_with_mentions?.forEach(s => {
      csv += `"${s.sentence}",${s.mention_count}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${mentionData.username}-mentions.csv`;
    a.click();
  };
  
  return (
    <div className="flex gap-4">
      <button
        onClick={handleExportJSON}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        Export JSON
      </button>
      <button
        onClick={handleExportCSV}
        className="px-4 py-2 bg-green-500 text-white rounded"
      >
        Export CSV
      </button>
    </div>
  );
}
```

### Integration 3: Mention Search Filter

```jsx
function MentionSearchFilter({ sentences }) {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredSentences = sentences.filter(s =>
    s.sentence.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div>
      <input
        type="text"
        placeholder="Search mentions..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full p-2 border rounded mb-4"
      />
      
      <div className="space-y-2">
        {filteredSentences.map((s, idx) => (
          <div key={idx} className="p-3 bg-slate-100 rounded">
            <p>{s.sentence}</p>
            <small className="text-slate-600">
              {s.mention_count} mention(s)
            </small>
          </div>
        ))}
      </div>
      
      {filteredSentences.length === 0 && (
        <p className="text-slate-500">No matches found</p>
      )}
    </div>
  );
}
```

---

## Testing Patterns

### Test 1: Unit Testing (Python)

```python
# test_mention_tracker.py
import pytest
from services.mention_tracker import MentionTracker

@pytest.fixture
def mention_tracker():
    return MentionTracker()

@pytest.mark.asyncio
async def test_track_mentions_basic(mention_tracker):
    username = "Shashank"
    transcript = "Shashank discussed the project. Shashank will handle it."
    
    result = await mention_tracker.track_mentions(
        username=username,
        full_transcript=transcript,
        segments=[]
    )
    
    assert result is not None
    assert result['mention_count'] == 2
    assert result['username'] == "Shashank"

@pytest.mark.asyncio
async def test_case_insensitive(mention_tracker):
    username = "shashank"
    transcript = "SHASHANK will do this."
    
    result = await mention_tracker.track_mentions(
        username=username,
        full_transcript=transcript,
        segments=[]
    )
    
    assert result['mention_count'] == 1

@pytest.mark.asyncio
async def test_no_mentions(mention_tracker):
    username = "Alice"
    transcript = "Shashank will handle this."
    
    result = await mention_tracker.track_mentions(
        username=username,
        full_transcript=transcript,
        segments=[]
    )
    
    assert result is None
```

### Test 2: Integration Test

```python
# test_api_mention_tracking.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_with_mention_tracking():
    with open("test_audio.wav", "rb") as f:
        response = client.post(
            "/api/v1/meetings/upload",
            files={"file": ("test.wav", f, "audio/wav")},
            params={"user_name": "Shashank"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "mention_tracking" in data
    mentions = data["mention_tracking"]
    
    assert mentions["username"] == "Shashank"
    assert mentions["mention_count"] > 0
    assert "highlight_transcript" in mentions
    assert "sentences_with_mentions" in mentions
```

### Test 3: E2E Test (JavaScript)

```javascript
// test/mention-tracking.e2e.js
describe('Mention Tracking E2E', () => {
  it('should track mentions and display in UI', async () => {
    // Upload audio with username
    const response = await uploadAudio(audioFile, 'Shashank');
    
    expect(response.mention_tracking).toBeDefined();
    expect(response.mention_tracking.mention_count).toBeGreaterThan(0);
    
    // Component should render
    const { getByText } = render(
      <MentionTracker mentionData={response.mention_tracking} />
    );
    
    expect(getByText(/Shashank/i)).toBeInTheDocument();
    expect(getByText(/Highlighted Transcript/i)).toBeInTheDocument();
  });
  
  it('should highlight mentions in transcript', () => {
    const { container } = render(
      <MentionTracker mentionData={mockMentionData} />
    );
    
    const highlights = container.querySelectorAll('[class*="yellow"]');
    expect(highlights.length).toBeGreaterThan(0);
  });
});
```

---

## Performance Optimization

### Optimization 1: Batch Processing

```python
async def batch_process_meetings(file_paths, username):
    """Process multiple files with same username"""
    
    import asyncio
    
    tasks = [
        upload_and_track(file_path, username)
        for file_path in file_paths
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Aggregate results
    total_mentions = sum(r['mention_count'] for r in results if r)
    all_tasks = []
    
    for result in results:
        if result and result.get('assigned_tasks'):
            all_tasks.extend(result['assigned_tasks'])
    
    return {
        "files_processed": len(file_paths),
        "total_mentions": total_mentions,
        "unique_tasks": len(set(t['task'] for t in all_tasks))
    }
```

### Optimization 2: Caching

```python
from functools import lru_cache

# Cache name variations to avoid regenerating
@lru_cache(maxsize=128)
def get_cached_name_variations(username: str):
    """Cache name variations"""
    tracker = MentionTracker()
    return tracker._generate_name_variations(username)

# Usage
variations = get_cached_name_variations("Shashank")
```

### Optimization 3: Progressive Loading

```jsx
// Frontend - show results as they arrive
function MentionTrackerProgressive({ mentionData, loading }) {
  return (
    <div>
      {mentionData?.username && (
        <div className="user-header">
          {mentionData.username}
        </div>
      )}
      
      {mentionData?.mention_count !== undefined && (
        <div className="stats">
          {mentionData.mention_count} mentions
        </div>
      )}
      
      {mentionData?.sentences_with_mentions && (
        <div className="sentences">
          {/* Render as available */}
        </div>
      )}
      
      {loading && <Spinner />}
    </div>
  );
}
```

---

## Summary

This guide covers:
- ✅ Basic usage patterns
- ✅ Advanced features and analysis
- ✅ Custom implementations
- ✅ Frontend integration patterns
- ✅ Testing strategies
- ✅ Performance optimizations

**Next Steps**:
1. Integrate with your specific workflow
2. Customize task patterns for your needs
3. Add to your analytics pipeline
4. Export to third-party tools

---

**Version**: 1.0 | **Updated**: January 29, 2026
