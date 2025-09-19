import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { v4 as uuidv4 } from 'uuid';
import {
  Box,
  Button,
  Tabs,
  Tab,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  useMediaQuery,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
  Alert,
  alpha,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Code as CodeIcon,
  Upload as UploadIcon,
  GitHub as GitHubIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  Folder as FolderIcon,
  FileCopy as FileCopyIcon,
  CloudUpload as CloudUploadIcon,
  CloudDownload as CloudDownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useAuth } from '@/contexts/AuthContext';

// Types
type Severity = 'error' | 'warning' | 'info' | 'success';

interface ReviewComment {
  id: string;
  lineNumber: number;
  severity: Severity;
  message: string;
  codeSnippet: string;
  suggestion?: string;
  category: string;
  timestamp: Date;
}

interface CodeFile {
  id: string;
  name: string;
  language: string;
  content: string;
  lastModified: Date;
}

const languageMap: Record<string, string> = {
  'js': 'javascript',
  'jsx': 'javascript',
  'ts': 'typescript',
  'tsx': 'typescript',
  'py': 'python',
  'java': 'java',
  'c': 'c',
  'cpp': 'cpp',
  'cs': 'csharp',
  'go': 'go',
  'rb': 'ruby',
  'php': 'php',
  'swift': 'swift',
  'kt': 'kotlin',
  'rs': 'rust',
  'sh': 'shell',
  'json': 'json',
  'yaml': 'yaml',
  'yml': 'yaml',
  'html': 'html',
  'css': 'css',
  'scss': 'scss',
  'sql': 'sql',
  'md': 'markdown',
};

const CodeReviewPage: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const editorRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<'code' | 'review' | 'suggestions'>('code');
  const [files, setFiles] = useState<CodeFile[]>([]);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [comments, setComments] = useState<ReviewComment[]>([]);
  const [githubDialogOpen, setGithubDialogOpen] = useState(false);
  const [githubRepoUrl, setGithubRepoUrl] = useState('');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: Severity }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number;
    mouseY: number;
    fileId: string | null;
  } | null>(null);

  // Sample data for demonstration
  useEffect(() => {
    const sampleFile: CodeFile = {
      id: 'sample-1',
      name: 'example.js',
      language: 'javascript',
      content: `// Example code with potential issues
function calculateTotal(items) {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price;
  }
  return total;
}

// Hardcoded credentials (security issue)
const API_KEY = '12345-abcde-67890-fghij';

// Inefficient array filtering
const activeUsers = users.filter(u => u.isActive).map(u => u.name);

// Unused variable
const unusedVar = 'This is not used';

// Missing error handling
function fetchData(url) {
  return fetch(url).then(response => response.json());
}

// Duplicate code
function calculateTax(amount) {
  return amount * 0.2;
}

function calculateTotalWithTax(amount) {
  return amount * 1.2;
}

// Complex function with multiple responsibilities
function processUserData(user) {
  // Validate user
  if (!user || !user.name || !user.email) {
    console.log('Invalid user');
    return;
  }
  
  // Process data
  const processedData = {
    ...user,
    name: user.name.trim(),
    email: user.email.toLowerCase(),
    processedAt: new Date().toISOString()
  };
  
  // Save to database
  saveToDatabase(processedData);
  
  // Send notification
  sendNotification(processedData.email, 'Profile updated');
  
  return processedData;
}`,
      lastModified: new Date(),
    };

    const sampleComments: ReviewComment[] = [
      {
        id: '1',
        lineNumber: 2,
        severity: 'info',
        message: 'Consider using Array.reduce() for summing values',
        codeSnippet: 'let total = 0;\nfor (let i = 0; i < items.length; i++) {\n  total += items[i].price;\n}\nreturn total;',
        suggestion: 'const total = items.reduce((sum, item) => sum + item.price, 0);',
        category: 'performance',
        timestamp: new Date(),
      },
      {
        id: '2',
        lineNumber: 9,
        severity: 'error',
        message: 'Hardcoded credentials detected',
        codeSnippet: "const API_KEY = '12345-abcde-67890-fghij';",
        suggestion: 'Use environment variables or a secure configuration management system',
        category: 'security',
        timestamp: new Date(),
      },
      {
        id: '3',
        lineNumber: 12,
        severity: 'warning',
        message: 'Inefficient array operations',
        codeSnippet: 'const activeUsers = users.filter(u => u.isActive).map(u => u.name);',
        suggestion: 'Use a single reduce operation to improve performance',
        category: 'performance',
        timestamp: new Date(),
      },
      {
        id: '4',
        lineNumber: 15,
        severity: 'warning',
        message: 'Unused variable',
        codeSnippet: "const unusedVar = 'This is not used';",
        suggestion: 'Remove the unused variable',
        category: 'code-quality',
        timestamp: new Date(),
      },
      {
        id: '5',
        lineNumber: 18,
        severity: 'warning',
        message: 'Missing error handling',
        codeSnippet: 'function fetchData(url) {\n  return fetch(url).then(response => response.json());\n}',
        suggestion: 'Add try/catch block and handle potential errors',
        category: 'error-handling',
        timestamp: new Date(),
      },
    ];

    setFiles([sampleFile]);
    setActiveFileId(sampleFile.id);
    setComments(sampleComments);
  }, []);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files;
    if (!fileList || fileList.length === 0) return;

    Array.from(fileList).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const extension = file.name.split('.').pop()?.toLowerCase() || '';
        const language = languageMap[extension] || 'plaintext';
        
        const newFile: CodeFile = {
          id: uuidv4(),
          name: file.name,
          language,
          content,
          lastModified: new Date(),
        };

        setFiles((prevFiles) => [...prevFiles, newFile]);
        setActiveFileId(newFile.id);
        setSnackbar({
          open: true,
          message: `File "${file.name}" uploaded successfully`,
          severity: 'success',
        });
      };
      reader.readAsText(file);
    });
  };

  const handleGithubImport = () => {
    if (!githubRepoUrl) {
      setSnackbar({
        open: true,
        message: 'Please enter a GitHub repository URL',
        severity: 'error',
      });
      return;
    }
    
    // TODO: Implement GitHub repository import
    setGithubDialogOpen(false);
    setSnackbar({
      open: true,
      message: 'Importing repository from GitHub...',
      severity: 'info',
    });
  };

  const handleReviewCode = () => {
    if (!activeFileId) return;
    
    setIsLoading(true);
    setActiveTab('review');
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setSnackbar({
        open: true,
        message: 'Code review completed',
        severity: 'success',
      });
    }, 1500);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: 'code' | 'review' | 'suggestions') => {
    setActiveTab(newValue);
  };

  const handleContextMenu = (event: React.MouseEvent, fileId: string) => {
    event.preventDefault();
    setContextMenu(
      contextMenu === null
        ? { mouseX: event.clientX - 2, mouseY: event.clientY - 4, fileId }
        : null,
    );
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  const handleDeleteFile = (fileId: string) => {
    setFiles((prevFiles) => {
      const newFiles = prevFiles.filter((file) => file.id !== fileId);
      if (activeFileId === fileId) {
        setActiveFileId(newFiles.length > 0 ? newFiles[0].id : null);
      }
      return newFiles;
    });
    handleCloseContextMenu();
  };

  const handleRenameFile = (fileId: string) => {
    // In a real app, you would show a dialog to enter a new name
    const newName = prompt('Enter new file name:');
    if (newName) {
      setFiles((prevFiles) =>
        prevFiles.map((file) =>
          file.id === fileId ? { ...file, name: newName } : file
        )
      );
    }
    handleCloseContextMenu();
  };

  const activeFile = files.find((file) => file.id === activeFileId);
  const filteredComments = comments.filter(
    (comment) => comment.lineNumber >= 1 && comment.lineNumber <= 50 // Just for demo
  );

  const getSeverityColor = (severity: Severity) => {
    switch (severity) {
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'info':
        return theme.palette.info.main;
      case 'success':
        return theme.palette.success.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getSeverityIcon = (severity: Severity) => {
    switch (severity) {
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'info':
        return <InfoIcon color="info" fontSize="small" />;
      case 'success':
        return <CheckCircleIcon color="success" fontSize="small" />;
      default:
        return <InfoIcon fontSize="small" />;
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          borderBottom: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Code Review
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
            multiple
          />
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => fileInputRef.current?.click()}
            size={isMobile ? 'small' : 'medium'}
          >
            {isMobile ? 'Upload' : 'Upload Files'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<GitHubIcon />}
            onClick={() => setGithubDialogOpen(true)}
            size={isMobile ? 'small' : 'medium'}
          >
            {isMobile ? 'GitHub' : 'Import from GitHub'}
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <CodeIcon />}
            onClick={handleReviewCode}
            disabled={isLoading || files.length === 0}
            size={isMobile ? 'small' : 'medium'}
          >
            {isLoading ? 'Reviewing...' : 'Review Code'}
          </Button>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* File Explorer */}
        <Box
          sx={{
            width: 250,
            borderRight: `1px solid ${theme.palette.divider}`,
            backgroundColor: theme.palette.background.paper,
            overflowY: 'auto',
            display: isMobile ? 'none' : 'block',
          }}
        >
          <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              FILES
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AddIcon />}
              fullWidth
              onClick={() => fileInputRef.current?.click()}
            >
              Add Files
            </Button>
          </Box>
          <List dense>
            {files.map((file) => (
              <ListItem
                key={file.id}
                button
                selected={activeFileId === file.id}
                onClick={() => setActiveFileId(file.id)}
                onContextMenu={(e) => handleContextMenu(e, file.id)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.08),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.primary.main, 0.12),
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <FileCopyIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      sx={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {file.name}
                    </Typography>
                  }
                  secondary={
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {file.language.toUpperCase()}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>

        {/* Editor/Review Panel */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {activeFile ? (
            <>
              <Tabs
                value={activeTab}
                onChange={handleTabChange}
                sx={{
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  minHeight: '48px',
                  '& .MuiTabs-flexContainer': {
                    height: '100%',
                  },
                }}
              >
                <Tab
                  label="Code"
                  value="code"
                  icon={<CodeIcon fontSize="small" />}
                  iconPosition="start"
                  sx={{ minHeight: '48px' }}
                />
                <Tab
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <span>Review</span>
                      {comments.length > 0 && (
                        <Chip
                          label={comments.length}
                          size="small"
                          sx={{
                            ml: 1,
                            height: 20,
                            '& .MuiChip-label': { px: 0.75 },
                          }}
                        />
                      )}
                    </Box>
                  }
                  value="review"
                  iconPosition="start"
                  sx={{ minHeight: '48px' }}
                  disabled={comments.length === 0}
                />
                <Tab
                  label="Suggestions"
                  value="suggestions"
                  iconPosition="start"
                  sx={{ minHeight: '48px' }}
                  disabled={comments.filter((c) => c.suggestion).length === 0}
                />
              </Tabs>

              <Box sx={{ flex: 1, overflow: 'hidden' }}>
                {activeTab === 'code' && (
                  <Editor
                    height="100%"
                    language={activeFile.language}
                    value={activeFile.content}
                    theme={theme.palette.mode === 'dark' ? 'vs-dark' : 'light'}
                    options={{
                      minimap: { enabled: !isMobile },
                      fontSize: 14,
                      wordWrap: 'on',
                      automaticLayout: true,
                      scrollBeyondLastLine: false,
                      readOnly: false,
                    }}
                    onMount={handleEditorDidMount}
                  />
                )}

                {activeTab === 'review' && (
                  <Box sx={{ height: '100%', overflowY: 'auto', p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Code Review Results
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {comments.length} issues found in your code
                    </Typography>

                    <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
                      {filteredComments.map((comment, index) => (
                        <React.Fragment key={comment.id}>
                          <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}>
                              {getSeverityIcon(comment.severity)}
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Box>
                                  <Typography
                                    variant="subtitle2"
                                    component="span"
                                    sx={{ fontWeight: 600, mr: 1 }}
                                  >
                                    Line {comment.lineNumber}:
                                  </Typography>
                                  <Typography variant="body2" component="span">
                                    {comment.message}
                                  </Typography>
                                </Box>
                              }
                              secondary={
                                <Box component="pre" sx={{ mt: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                                  <code>{comment.codeSnippet}</code>
                                </Box>
                              }
                              secondaryTypographyProps={{ component: 'div' }}
                            />
                          </ListItem>
                          {index < filteredComments.length - 1 && <Divider component="li" />}
                        </React.Fragment>
                      ))}
                    </List>
                  </Box>
                )}

                {activeTab === 'suggestions' && (
                  <Box sx={{ height: '100%', overflowY: 'auto', p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Suggested Improvements
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {comments.filter((c) => c.suggestion).length} suggestions available
                    </Typography>

                    <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
                      {comments
                        .filter((comment) => comment.suggestion)
                        .map((comment, index, arr) => (
                          <React.Fragment key={comment.id}>
                            <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                              <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}>
                                <AutoFixHighIcon color="primary" fontSize="small" />
                              </ListItemIcon>
                              <ListItemText
                                primary={
                                  <Box>
                                    <Typography
                                      variant="subtitle2"
                                      component="span"
                                      sx={{ fontWeight: 600, mr: 1 }}
                                    >
                                      Line {comment.lineNumber}:
                                    </Typography>
                                    <Typography variant="body2" component="span">
                                      {comment.message}
                                    </Typography>
                                  </Box>
                                }
                                secondary={
                                  <Box>
                                    <Typography variant="caption" color="text.secondary" display="block" mt={1} mb={0.5}>
                                      Current code:
                                    </Typography>
                                    <Box
                                      component="pre"
                                      sx={{
                                        mt: 0.5,
                                        p: 1,
                                        bgcolor: 'action.hover',
                                        borderRadius: 1,
                                        mb: 1.5,
                                      }}
                                    >
                                      <code>{comment.codeSnippet}</code>
                                    </Box>
                                    <Typography variant="caption" color="text.secondary" display="block" mb={0.5}>
                                      Suggestion:
                                    </Typography>
                                    <Box
                                      component="pre"
                                      sx={{
                                        mt: 0.5,
                                        p: 1,
                                        bgcolor: alpha(theme.palette.primary.main, 0.05),
                                        borderLeft: `3px solid ${theme.palette.primary.main}`,
                                        borderRadius: '0 4px 4px 0',
                                      }}
                                    >
                                      <code>{comment.suggestion}</code>
                                    </Box>
                                  </Box>
                                }
                                secondaryTypographyProps={{ component: 'div' }}
                              />
                            </ListItem>
                            {index < arr.length - 1 && <Divider component="li" sx={{ my: 1 }} />}
                          </React.Fragment>
                        ))}
                    </List>
                  </Box>
                )}
              </Box>
            </>
          ) : (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                p: 3,
                textAlign: 'center',
                color: 'text.secondary',
              }}
            >
              <CodeIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                No file selected
              </Typography>
              <Typography variant="body1" paragraph>
                Upload a file or import from GitHub to get started with code review.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<CloudUploadIcon />}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Upload Files
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<GitHubIcon />}
                  onClick={() => setGithubDialogOpen(true)}
                >
                  Import from GitHub
                </Button>
              </Box>
            </Box>
          )}
        </Box>
      </Box>

      {/* GitHub Import Dialog */}
      <Dialog open={githubDialogOpen} onClose={() => setGithubDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import from GitHub</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Enter the URL of a GitHub repository to import code for review.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="GitHub Repository URL"
            type="url"
            fullWidth
            variant="outlined"
            placeholder="https://github.com/username/repository"
            value={githubRepoUrl}
            onChange={(e) => setGithubRepoUrl(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGithubDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleGithubImport} variant="contained" color="primary">
            Import
          </Button>
        </DialogActions>
      </Dialog>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={handleCloseContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={() => handleRenameFile(contextMenu?.fileId || '')}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Rename</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDeleteFile(contextMenu?.fileId || '')}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText primaryTypographyProps={{ color: 'error' }}>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Snackbar Notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodeReviewPage;
