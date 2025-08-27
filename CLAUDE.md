# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cclog is a Claude Code Log Browser - a shell utility that allows browsing and viewing Claude Code conversation history using fzf. The project provides an interactive interface to explore conversation logs, resume sessions, and navigate between projects.

## Architecture

The project consists of several key components:

### Core Components

- `cclog.sh` - Main shell script providing the cclog command interface and subcommands
- `cclog_helper.py` - Python helper script for performance-optimized parsing of JSONL conversation files
- `cclog.plugin.zsh` - Zsh plugin wrapper for easy installation via plugin managers
- `claude-projects-jsonl-specification.md` - Detailed specification of Claude Code's JSONL file format

### Key Functions (cclog_helper.py)

- `SessionSummary` - Data class for session metadata (path, messages count, duration, etc.)
- `parse_session_minimal()` - Efficiently parses JSONL files to extract session metadata
- `get_session_list()` - Lists sessions for current directory with filtering and sorting
- `get_projects_list()` - Discovers and lists all Claude Code projects across the system
- `decode_project_path()` - Converts encoded directory names back to original paths
- `view_session()` - Formats and displays conversation content with color coding

### File Format Understanding

The project handles three types of JSONL files in `~/.claude/projects/`:
1. **Conversation files** - Full conversation history with timestamps
2. **Summary files** - Topic summaries only (no timestamps)  
3. **Mixed files** - Start with summaries, followed by conversation entries

## Development Commands

### Testing
```bash
# Run full test suite
./run_tests.sh

# Or manually with pytest
pytest tests/ -v
```

### Manual Testing
```bash
# Test session listing
cclog

# Test project browsing  
cclog projects

# Test file viewing
cclog view ~/.claude/projects/*/session-id.jsonl

# Test session info
cclog info ~/.claude/projects/*/session-id.jsonl
```

## Key Implementation Details

### Performance Optimization
- Uses Python helper script for parsing large JSONL files (some files can be 1000+ lines)
- Stream-based processing to handle large conversation histories efficiently
- Caching of decoded project paths to avoid repeated filesystem operations

### Directory Encoding
Claude Code encodes project paths by converting:
- `/` → `-`
- `.` → `-`

Example: `/Users/username/project` → `-Users-username-project/`

The `decode_project_path()` function progressively tries different segment combinations to restore original paths.

### Message Types
The parser handles different entry types:
- `type: "user"` - User messages
- `type: "assistant"` - Assistant responses and tool usage
- `type: "summary"` - Topic summaries with `leafUuid` references

### Color Coding
- User messages: Cyan
- Assistant messages: White  
- Tool usage: Gray
- Summaries: With 📑 prefix when available

## Requirements

- `fzf` - Fuzzy finder for interactive browsing
- `python3` - For performance optimization (fallback available but slower)
- `claude` - Claude Code CLI for resume functionality

## Testing Structure

Tests are organized in `tests/` with:
- `test_cclog_helper.py` - Main Python helper function tests
- `test_decode_project_path.py` - Path decoding logic tests
- `fixtures/` - Various JSONL file formats for testing edge cases