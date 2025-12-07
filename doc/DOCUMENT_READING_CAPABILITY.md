# Document Reading Capability for AI Agents

## Overview

AI agents now have the capability to read various document formats (PDF, Word, Excel, PowerPoint, images, etc.) through both MCP services and standalone functions. This enables agents to:

1. **Read JIRA attachments** directly without downloading
2. **Read local files** in various formats
3. **Process documents** as markdown for easy consumption

## Supported File Formats

### Document Formats
- **PDF** (`.pdf`)
- **Microsoft Word** (`.docx`, `.doc`)
- **Microsoft Excel** (`.xlsx`, `.xls`)
- **Microsoft PowerPoint** (`.pptx`, `.ppt`)

### Data Formats
- **CSV** (`.csv`)
- **JSON** (`.json`)
- **XML** (`.xml`)
- **HTML** (`.html`, `.htm`)

### Image Formats
- **JPEG** (`.jpg`, `.jpeg`)
- **PNG** (`.png`)
- **BMP** (`.bmp`)
- **TIFF** (`.tiff`, `.tif`)

### Other Formats
- **Audio** (`.wav`, `.mp3`)
- **EPUB** (`.epub`)
- **ZIP** (`.zip`)
- **Text** (`.txt`, `.md`)

## MCP Tools for AI Agents

### 1. `read_file` - Read Local Files

Read and convert local files to markdown format.

**Usage:**
```json
{
  "tool": "read_file",
  "arguments": {
    "file_path": "/path/to/document.pdf"
  }
}
```

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 123456,
  "markdown": "# Document Content\n\nConverted markdown text..."
}
```

### 2. `jira_read_attachment_content` - Read JIRA Attachments

Download and convert JIRA attachments to markdown without saving to disk.

**Usage:**
```json
{
  "tool": "jira_read_attachment_content",
  "arguments": {
    "issue_key": "SCRUM-7",
    "filename": "2017-Scrum-Guide-US.pdf"
  }
}
```

**With Multiple Files (Same Name):**
```json
{
  "tool": "jira_read_attachment_content",
  "arguments": {
    "issue_key": "SCRUM-7",
    "filename": "requirements.pdf",
    "attachment_id": "12345"
  }
}
```

**Response:**
```json
{
  "success": true,
  "filename": "2017-Scrum-Guide-US.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 595968,
  "issue_key": "SCRUM-7",
  "attachment_id": "10001",
  "markdown": "# The Scrum Guide™\n\nThe Definitive Guide to Scrum..."
}
```

## Python API for Developers

### Async Operations (Recommended for MCP)

```python
from document_converter import convert_file_async, convert_to_markdown_async

# Read local file
result = await convert_file_async('/path/to/document.pdf')
if result['success']:
    markdown_content = result['markdown']

# Read from byte stream
with open('file.docx', 'rb') as f:
    result = await convert_to_markdown_async(
        f, 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'file.docx'
    )
```

### Synchronous Operations

```python
from document_converter import convert_file, convert_to_markdown

# Read local file
result = convert_file('/path/to/document.pdf')
if result['success']:
    markdown_content = result['markdown']

# Read from byte stream
with open('file.xlsx', 'rb') as f:
    result = convert_to_markdown(
        f,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'file.xlsx'
    )
```

### JIRA Client Integration

```python
from jira_client import JiraClientAsync

client = JiraClientAsync(url, username, api_token)

# Read JIRA attachment content
result = await client.read_attachment_content(
    issue_key='SCRUM-7',
    filename='2017-Scrum-Guide-US.pdf'
)

if result['success']:
    markdown_content = result['markdown']
```

## Architecture

### Component Flow

```
AI Agent Request
    ↓
MCP Server (mcp_server.py)
    ↓
┌─────────────────────┬──────────────────────┐
│   read_file tool    │  jira_read_*  tool   │
└──────────┬──────────┴──────────┬───────────┘
           ↓                     ↓
    DocumentConverter      JiraClientAsync
           ↓                     ↓
       MarkItDown         DocumentConverter
           ↓                     ↓
    Markdown Output ←──────── Markdown Output
```

### Key Components

1. **document_converter.py**
   - Core conversion logic using MarkItDown library
   - Supports both sync and async operations
   - MIME type detection from file extensions
   - File size validation (50MB limit)

2. **jira_client.py**
   - `read_attachment_content()` method
   - Fetches JIRA attachments via REST API
   - Integrates with DocumentConverter
   - Handles attachment disambiguation

3. **mcp_server.py**
   - Exposes `read_file` MCP tool
   - Exposes `jira_read_attachment_content` MCP tool
   - Handles tool invocations
   - Returns JSON-formatted responses

## Error Handling

### Common Error Scenarios

1. **File Not Found**
```json
{
  "success": false,
  "error": "File does not exist: /path/to/file.pdf",
  "filename": "file.pdf"
}
```

2. **Unsupported Format**
```json
{
  "success": false,
  "error": "Unsupported file type: application/x-unknown",
  "mime_type": "application/x-unknown"
}
```

3. **File Too Large**
```json
{
  "success": false,
  "error": "File too large (75.3MB). Maximum size: 50MB"
}
```

4. **Conversion Failed**
```json
{
  "success": false,
  "error": "Conversion failed: Invalid PDF structure"
}
```

5. **JIRA Attachment Not Found**
```json
{
  "success": false,
  "error": "Attachment \"missing.pdf\" not found in SCRUM-7",
  "available_attachments": ["doc1.pdf", "doc2.docx"]
}
```

## Installation

Install the required dependency:

```bash
pip install markitdown
```

Or install all dependencies:

```bash
pip install -r script/requirements.txt
```

## Use Cases

### 1. Business Analysis Agent
Read requirements documents, user stories, and specifications from JIRA attachments.

```python
# Agent workflow
issue = await get_jira_issue("SCRUM-7")
for attachment in issue['attachments']:
    content = await read_attachment_content("SCRUM-7", attachment['filename'])
    analyze_requirements(content['markdown'])
```

### 2. Documentation Agent
Process and summarize PDF guides, Word documents, and presentations.

```python
# Read Scrum Guide
guide = await read_attachment_content("SCRUM-7", "2017-Scrum-Guide-US.pdf")
summary = summarize_document(guide['markdown'])
await add_comment("SCRUM-7", f"Summary: {summary}")
```

### 3. Data Analysis Agent
Read Excel spreadsheets and CSV files for data processing.

```python
# Read data file
data = await read_file("/path/to/data.xlsx")
insights = analyze_data(data['markdown'])
```

### 4. Code Review Agent
Read source code and technical documents from local files.

```python
# Read architecture document
doc = await read_file("./doc/architecture/system-design.pdf")
review = review_architecture(doc['markdown'])
```

## Limitations

1. **File Size**: Maximum 50MB per file
2. **Conversion Quality**: Depends on source document structure
3. **Complex Layouts**: Tables and graphics may not convert perfectly
4. **Security**: Only reads files accessible to the process user
5. **Dependency**: Requires `markitdown` library installation

## Future Enhancements

- [ ] Support for larger files with streaming
- [ ] OCR for scanned PDF documents
- [ ] Better table structure preservation
- [ ] Image extraction and description
- [ ] Audio transcription
- [ ] Batch file processing
- [ ] Custom conversion templates

## Related Documentation

- [JIRA MCP Server Architecture](architecture/)
- [Document Converter Module](../src/document_converter.py)
- [JIRA Client API](../src/jira_client.py)
- [MCP Server Implementation](../src/mcp_server.py)
