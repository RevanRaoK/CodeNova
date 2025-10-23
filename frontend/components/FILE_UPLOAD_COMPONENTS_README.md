# File Upload and Analysis Components

This document describes the implementation of Task 5: File upload and analysis components for the CodeNova platform enhancements.

## Overview

This implementation provides a complete set of components for multi-file upload, batch analysis, and enhanced feedback mechanisms. All components are designed to work together seamlessly while remaining modular and reusable.

## Components

### 1. MultiFileUploadZone

**Location:** `frontend/components/MultiFileUploadZone.jsx`

**Purpose:** Enhanced file upload component with drag-drop, progress tracking, and validation.

**Features:**
- Drag-and-drop file upload
- Multiple file selection
- Real-time file validation
- Individual file progress tracking
- File size and type validation
- Retry mechanism for failed uploads
- Language auto-detection from filename

**Usage:**
```jsx
import MultiFileUploadZone from './components/MultiFileUploadZone';

<MultiFileUploadZone
  onUploadComplete={(result) => console.log(result)}
  onClose={() => setShowUpload(false)}
  maxFiles={10}
/>
```

**Props:**
- `onUploadComplete`: Callback when upload completes
- `onClose`: Callback to close the modal
- `maxFiles`: Maximum number of files allowed (default: 10)

### 2. FilenamePromptModal

**Location:** `frontend/components/FilenamePromptModal.jsx`

**Purpose:** Modal for prompting user to enter filename before analysis with language auto-detection.

**Features:**
- Filename input with validation
- Automatic language detection based on file extension
- Suggested extensions based on code content
- Real-time validation feedback
- Support for all major programming languages

**Usage:**
```jsx
import FilenamePromptModal from './components/FilenamePromptModal';

<FilenamePromptModal
  onSubmit={(filename, language) => handleAnalyze(filename, language)}
  onClose={() => setShowModal(false)}
  initialFilename="app.js"
  code={codeContent}
/>
```

**Props:**
- `onSubmit`: Callback with filename and detected language
- `onClose`: Callback to close the modal
- `initialFilename`: Pre-filled filename (optional)
- `code`: Code content for extension suggestions (optional)

### 3. BatchUploadProgress

**Location:** `frontend/components/BatchUploadProgress.jsx`

**Purpose:** Real-time progress tracker for batch file uploads and analysis.

**Features:**
- Real-time status updates via polling
- Progress bar with percentage
- Individual file status tracking
- Processing time display
- Estimated completion time
- Detailed error messages

**Usage:**
```jsx
import BatchUploadProgress from './components/BatchUploadProgress';

<BatchUploadProgress
  batchId="batch-uuid"
  onComplete={(status) => console.log(status)}
  onClose={() => setShowProgress(false)}
/>
```

**Props:**
- `batchId`: Batch ID to track
- `onComplete`: Callback when batch completes
- `onClose`: Callback to close the modal

### 4. SuggestionFeedbackWidget

**Location:** `frontend/components/SuggestionFeedbackWidget.jsx`

**Purpose:** Widget for accepting, rejecting, or modifying AI suggestions.

**Features:**
- Accept/Reject/Modify actions
- Inline modification input
- Optional comments
- Success/error feedback
- Compact mode for space-constrained layouts

**Usage:**
```jsx
import SuggestionFeedbackWidget from './components/SuggestionFeedbackWidget';

<SuggestionFeedbackWidget
  suggestion={issueObject}
  onFeedbackSubmit={(data) => console.log(data)}
  disabled={false}
  compact={false}
/>
```

**Props:**
- `suggestion`: Suggestion/issue object with id
- `onFeedbackSubmit`: Callback when feedback is submitted
- `disabled`: Disable all actions
- `compact`: Use compact layout

### 5. SuggestionDisplay

**Location:** `frontend/components/SuggestionDisplay.jsx`

**Purpose:** Display AI suggestions with code diff viewer, separating descriptive text from code.

**Features:**
- Separate display of text and code
- Syntax highlighting for code blocks
- Side-by-side diff view
- Copy code functionality
- Support for multiple code blocks
- Inline code highlighting
- Expandable/collapsible view

**Usage:**
```jsx
import SuggestionDisplay from './components/SuggestionDisplay';

<SuggestionDisplay
  suggestion={issueObject}
  originalCode={originalCodeString}
  showDiff={true}
  compact={false}
/>
```

**Props:**
- `suggestion`: Suggestion object with message/suggestion text
- `originalCode`: Original code for diff comparison (optional)
- `showDiff`: Show side-by-side diff view
- `compact`: Use compact collapsible layout

### 6. Enhanced CodeEditor

**Location:** `frontend/components/CodeEditor.jsx`

**Purpose:** Enhanced code editor that requires filename before analysis.

**Features:**
- Filename requirement before analysis
- Integrated filename modal
- Analyze button
- Clear button
- Filename display in header
- Language detection

**Usage:**
```jsx
import { CodeEditor } from './components/CodeEditor';

<CodeEditor
  code={code}
  setCode={setCode}
  language="javascript"
  onAnalyze={(code, lang, filename) => handleAnalyze(code, lang, filename)}
  requireFilename={true}
  filename={filename}
  onFilenameChange={setFilename}
/>
```

**Props:**
- `code`: Code content
- `setCode`: Callback to update code
- `language`: Programming language
- `readOnly`: Make editor read-only
- `onAnalyze`: Callback when analyze is clicked
- `requireFilename`: Require filename before analysis
- `filename`: Current filename
- `onFilenameChange`: Callback when filename changes

### 7. AnalysisHistory

**Location:** `frontend/components/AnalysisHistory.jsx`

**Purpose:** Display user's analysis history with filenames and batch analyses.

**Features:**
- Paginated list of analyses
- Filename display for each analysis
- Status badges (completed, failed, processing)
- Issue count summary
- Language and date filters
- Expandable details
- Delete functionality
- Relative time display

**Usage:**
```jsx
import AnalysisHistory from './components/AnalysisHistory';

<AnalysisHistory
  onAnalysisSelect={(analysis) => viewAnalysis(analysis)}
  enableFeedback={true}
/>
```

**Props:**
- `onAnalysisSelect`: Callback when analysis is selected
- `enableFeedback`: Enable feedback widgets in expanded view

### 8. AIResponseParser Utility

**Location:** `frontend/utils/AIResponseParser.js`

**Purpose:** Utility to parse AI responses and separate code from text.

**Features:**
- Extract markdown code blocks
- Extract inline code
- Remove code from text
- Parse suggestions and issues
- Detect code in text
- Format code blocks
- Split text into paragraphs

**Usage:**
```javascript
import AIResponseParser from '../utils/AIResponseParser';

// Parse raw AI response
const parsed = AIResponseParser.parseResponse(rawText);
console.log(parsed.description); // Text without code
console.log(parsed.codeBlocks); // Array of code blocks

// Parse suggestion object
const suggestion = AIResponseParser.parseSuggestion(issueObject);
console.log(suggestion.text); // Description text
console.log(suggestion.code); // Extracted code

// Check if text contains code
const hasCode = AIResponseParser.containsCode(text);

// Remove code from text
const textOnly = AIResponseParser.removeCode(text);
```

**Methods:**
- `parseResponse(rawResponse)`: Parse raw text into components
- `parseSuggestion(suggestion)`: Parse suggestion object
- `extractCodeSnippets(text)`: Extract all code snippets
- `removeCode(text)`: Remove code, keep text only
- `formatCodeBlock(code, language)`: Format code as markdown
- `parseIssue(issue)`: Parse issue object
- `parseIssues(issues)`: Parse array of issues
- `containsCode(text)`: Check if text has code
- `splitIntoParagraphs(text)`: Split preserving code blocks
- `cleanText(text)`: Clean and normalize text

## Integration

### Exporting Components

All components are exported from a central file:

```javascript
// frontend/components/FileUploadComponents.js
export { default as MultiFileUploadZone } from './MultiFileUploadZone';
export { default as FilenamePromptModal } from './FilenamePromptModal';
export { default as BatchUploadProgress } from './BatchUploadProgress';
export { default as SuggestionFeedbackWidget } from './SuggestionFeedbackWidget';
export { default as SuggestionDisplay } from './SuggestionDisplay';
export { default as AnalysisHistory } from './AnalysisHistory';
export { CodeEditor } from './CodeEditor';
```

### Demo Page

A complete demo page is available at `frontend/pages/FileUploadDemo.jsx` that demonstrates all components.

## Requirements Coverage

This implementation covers the following requirements from the spec:

### Requirement 1.1-1.5: Multi-File Upload and Background Analysis
- ✅ Multi-file upload with queue display
- ✅ Background job initiation
- ✅ Filename preservation and association
- ✅ Filename display in history
- ✅ Multiple file queuing without blocking UI

### Requirement 2.1-2.4: Filename Requirement for Monaco Editor
- ✅ Filename prompt before analysis
- ✅ Filename association with results
- ✅ Display in history
- ✅ Validation and error messages

### Requirement 3.1-3.5: Enhanced Analysis History with Feedback
- ✅ Display all analyses with filenames
- ✅ Display all suggestions
- ✅ Accept/reject/modify interface
- ✅ Feedback capture and storage
- ✅ Status updates

### Requirement 6.1-6.4: AI Suggestion Output Refinement
- ✅ Pure descriptive text without embedded code
- ✅ Code extraction from AI responses
- ✅ Dedicated UI component for code
- ✅ Diff viewer with syntax highlighting
- ✅ Clear separation of elements

### Requirement 12.1: Input Validation
- ✅ File type validation
- ✅ File size validation
- ✅ Clear error messages

### Requirement 13.1-13.3: Real-Time Job Status Updates
- ✅ Processing state display
- ✅ Real-time updates via polling
- ✅ Automatic status refresh
- ✅ Current status display

## Dependencies

These components depend on:

- **Services:**
  - `analysisService.js` - For file upload and analysis operations
  - `feedbackService.js` - For feedback submission

- **Icons:**
  - `lucide-react` - For all icons

- **Utilities:**
  - `AIResponseParser.js` - For parsing AI responses

## Testing

To test the components:

1. Navigate to `/file-upload-demo` (add route in your router)
2. Test each component individually
3. Verify file upload flow
4. Test feedback submission
5. Check analysis history display

## Future Enhancements

Potential improvements:

1. WebSocket support for real-time updates (currently uses polling)
2. Drag-and-drop reordering of files in queue
3. Bulk feedback actions
4. Export analysis results
5. Advanced filtering and search in history
6. Syntax highlighting in diff viewer
7. Keyboard shortcuts for feedback actions

## Notes

- All components are designed to be responsive and mobile-friendly
- Error handling is implemented throughout
- Loading states are provided for all async operations
- Components follow React best practices and hooks patterns
- Accessibility features are included where applicable
