#!/usr/bin/env python3

import json
import os
import tempfile
import unittest
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cclog_helper import export_markdown, format_markdown_message, export_markdown_filtered, filter_empty_messages, export_all_sessions_filtered


class TestExportMarkdown(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_session_file = os.path.join(self.temp_dir, "test_session.jsonl")
        
        # Create a test session file
        test_data = [
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": "Hello, can you help me?"
                },
                "timestamp": "2025-01-15T10:30:00.000Z",
                "uuid": "user-uuid-1",
                "sessionId": "test-session-123"
            },
            {
                "type": "assistant", 
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Hello! I'd be happy to help you."}]
                },
                "timestamp": "2025-01-15T10:30:05.000Z",
                "uuid": "assistant-uuid-1",
                "sessionId": "test-session-123"
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant", 
                    "content": [{
                        "type": "tool_use",
                        "id": "toolu_123",
                        "name": "bash",
                        "input": {"command": "ls -la"}
                    }]
                },
                "timestamp": "2025-01-15T10:30:10.000Z",
                "uuid": "assistant-uuid-2",
                "sessionId": "test-session-123"
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{
                        "tool_use_id": "toolu_123",
                        "type": "tool_result",
                        "content": [{"type": "text", "text": "total 8\ndrwxr-xr-x  3 user  staff   96 Jan 15 10:30 .\ndrwxr-xr-x  4 user  staff  128 Jan 15 10:29 .."}]
                    }]
                },
                "toolUseResult": [{"type": "text", "text": "total 8\ndrwxr-xr-x  3 user  staff   96 Jan 15 10:30 .\ndrwxr-xr-x  4 user  staff  128 Jan 15 10:29 .."}],
                "timestamp": "2025-01-15T10:30:12.000Z",
                "uuid": "user-uuid-2",
                "sessionId": "test-session-123"
            }
        ]
        
        with open(self.test_session_file, "w") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_format_markdown_message_user(self):
        """Test formatting user messages"""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": "Test user message"
            },
            "timestamp": "2025-01-15T10:30:00.000Z"
        }
        
        result = format_markdown_message(data)
        self.assertIn("## User (10:30:00)", result)
        self.assertIn("Test user message", result)

    def test_format_markdown_message_assistant(self):
        """Test formatting assistant messages"""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant", 
                "content": [{"type": "text", "text": "Test assistant response"}]
            },
            "timestamp": "2025-01-15T10:30:05.000Z"
        }
        
        result = format_markdown_message(data)
        self.assertIn("## Assistant (10:30:05)", result)
        self.assertIn("Test assistant response", result)

    def test_format_markdown_message_tool_use(self):
        """Test formatting tool use messages"""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "bash",
                    "input": {"command": "ls -la"}
                }]
            },
            "timestamp": "2025-01-15T10:30:10.000Z"
        }
        
        result = format_markdown_message(data)
        self.assertIn("## Assistant (10:30:10)", result)
        self.assertIn("### Tool: bash", result)
        self.assertIn("```json", result)
        self.assertIn('"command": "ls -la"', result)

    def test_format_markdown_message_tool_result(self):
        """Test formatting tool result messages"""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{
                    "tool_use_id": "toolu_123",
                    "type": "tool_result",
                    "content": [{"type": "text", "text": "command output"}]
                }]
            },
            "toolUseResult": [{"type": "text", "text": "command output"}],
            "timestamp": "2025-01-15T10:30:12.000Z"
        }
        
        result = format_markdown_message(data)
        self.assertIn("## User (10:30:12)", result)
        self.assertIn("### Tool Result", result)
        self.assertIn("```\ncommand output\n```", result)

    def test_export_markdown_creates_file(self):
        """Test that export_markdown creates a Markdown file"""
        output_dir = os.path.join(self.temp_dir, "export_test")
        
        success = export_markdown(self.test_session_file, output_dir)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_dir))
        
        # Check that a file was created
        files = os.listdir(output_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith('.md'))

    def test_export_markdown_file_content(self):
        """Test the content of exported Markdown file"""
        output_dir = os.path.join(self.temp_dir, "export_test")
        
        success = export_markdown(self.test_session_file, output_dir)
        self.assertTrue(success)
        
        # Read the exported file
        files = os.listdir(output_dir)
        output_file = os.path.join(output_dir, files[0])
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that the file contains expected sections
        self.assertIn("# Claude Code Session test_session", content)
        self.assertIn("**Date**: 2025-01-15", content)
        self.assertIn("**Messages**: 4", content)
        self.assertIn("## User (10:30:00)", content)
        self.assertIn("Hello, can you help me?", content)
        self.assertIn("## Assistant (10:30:05)", content)
        self.assertIn("Hello! I'd be happy to help you.", content)
        self.assertIn("### Tool: bash", content)
        self.assertIn("### Tool Result", content)

    def test_export_markdown_invalid_file(self):
        """Test export with invalid file path"""
        invalid_file = "/nonexistent/path/file.jsonl"
        output_dir = os.path.join(self.temp_dir, "export_test")
        
        success = export_markdown(invalid_file, output_dir)
        
        self.assertFalse(success)

    def test_export_markdown_default_output_dir(self):
        """Test export with default output directory"""
        # Change to temp directory to avoid creating claude_chat in real filesystem
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            success = export_markdown(self.test_session_file)
            self.assertTrue(success)
            
            # Check that default directory was created
            self.assertTrue(os.path.exists("claude_chat"))
            files = os.listdir("claude_chat")
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].endswith('.md'))
        finally:
            os.chdir(original_cwd)

    def test_filter_empty_messages(self):
        """Test filtering of empty messages"""
        markdown_content = [
            "# Test Session",
            "",
            "## User (10:30:00)",
            "",
            "Hello",
            "",
            "## Assistant (10:30:01)",
            "",
            "",  # Empty content - should be filtered
            "## User (10:30:02)",
            "",
            "How are you?",
            "",
            "## Assistant (10:30:03)",
            "",
            "I'm good, thanks!",
            "",
            "## User (10:30:04)",
            "",
            "### Tool Result",
            "",
            "",  # Empty tool result - should be filtered
            "## Assistant (10:30:05)",
            "",
            "Final response"
        ]
        
        filtered = filter_empty_messages(markdown_content)
        
        # Should keep non-message headers and non-empty messages only
        self.assertIn("# Test Session", filtered)
        self.assertIn("## User (10:30:00)", filtered)
        self.assertIn("Hello", filtered)
        self.assertNotIn("## Assistant (10:30:01)", filtered)  # Empty assistant message
        self.assertIn("## User (10:30:02)", filtered)
        self.assertIn("How are you?", filtered)
        self.assertIn("## Assistant (10:30:03)", filtered)
        self.assertIn("I'm good, thanks!", filtered)
        self.assertNotIn("## User (10:30:04)", filtered)  # Empty tool result
        self.assertIn("## Assistant (10:30:05)", filtered)
        self.assertIn("Final response", filtered)

    def test_export_markdown_filtered_creates_file(self):
        """Test that export_markdown_filtered creates a Markdown file"""
        output_dir = os.path.join(self.temp_dir, "filtered_export_test")
        
        success = export_markdown_filtered(self.test_session_file, output_dir)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_dir))
        
        # Check that a file was created with _filtered suffix
        files = os.listdir(output_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith('.md'))
        self.assertIn('_filtered_', files[0])

    def test_export_markdown_filtered_file_content(self):
        """Test the content of exported filtered Markdown file"""
        output_dir = os.path.join(self.temp_dir, "filtered_export_test")
        
        success = export_markdown_filtered(self.test_session_file, output_dir)
        self.assertTrue(success)
        
        # Read the exported file
        files = os.listdir(output_dir)
        output_file = os.path.join(output_dir, files[0])
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that the file contains expected sections and title includes (Filtered)
        self.assertIn("# Claude Code Session test_session (Filtered)", content)
        self.assertIn("**Date**: 2025-01-15", content)
        self.assertIn("**Messages**: 4", content)
        self.assertIn("## User (10:30:00)", content)
        self.assertIn("Hello, can you help me?", content)
        self.assertIn("## Assistant (10:30:05)", content)
        self.assertIn("Hello! I'd be happy to help you.", content)

    def test_export_markdown_filtered_with_empty_messages(self):
        """Test filtered export with a session containing empty messages"""
        # Create a test file with empty messages
        test_file_with_empties = os.path.join(self.temp_dir, "test_session_empties.jsonl")
        test_data = [
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": "Hello"
                },
                "timestamp": "2025-01-15T10:30:00.000Z",
                "uuid": "user-uuid-1",
                "sessionId": "test-session-123"
            },
            {
                "type": "assistant", 
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": ""}]  # Empty response
                },
                "timestamp": "2025-01-15T10:30:01.000Z",
                "uuid": "assistant-uuid-1",
                "sessionId": "test-session-123"
            },
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": "Are you there?"
                },
                "timestamp": "2025-01-15T10:30:02.000Z",
                "uuid": "user-uuid-2",
                "sessionId": "test-session-123"
            },
            {
                "type": "assistant", 
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Yes, I'm here!"}]
                },
                "timestamp": "2025-01-15T10:30:03.000Z",
                "uuid": "assistant-uuid-2",
                "sessionId": "test-session-123"
            }
        ]
        
        with open(test_file_with_empties, "w") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")
        
        output_dir = os.path.join(self.temp_dir, "filtered_empty_test")
        success = export_markdown_filtered(test_file_with_empties, output_dir)
        self.assertTrue(success)
        
        # Read the exported file
        files = os.listdir(output_dir)
        output_file = os.path.join(output_dir, files[0])
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain the non-empty messages only
        self.assertIn("## User (10:30:00)", content)
        self.assertIn("Hello", content)
        self.assertIn("## User (10:30:02)", content) 
        self.assertIn("Are you there?", content)
        self.assertIn("## Assistant (10:30:03)", content)
        self.assertIn("Yes, I'm here!", content)
        
        # Should not contain the empty assistant response timestamp
        self.assertNotIn("## Assistant (10:30:01)", content)

    def test_export_all_sessions_filtered(self):
        """Test bulk export of all sessions with filtering"""
        # Create a test directory with multiple session files
        test_sessions_dir = os.path.join(self.temp_dir, "test_sessions")
        os.makedirs(test_sessions_dir)
        
        # Create multiple test session files
        session_files = []
        for i in range(3):
            session_file = os.path.join(test_sessions_dir, f"session_{i+1}.jsonl")
            test_data = [
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": f"Hello from session {i+1}"
                    },
                    "timestamp": "2025-01-15T10:30:00.000Z",
                    "uuid": f"user-uuid-{i+1}",
                    "sessionId": f"test-session-{i+1}"
                },
                {
                    "type": "assistant", 
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": f"Response from session {i+1}"}]
                    },
                    "timestamp": "2025-01-15T10:30:05.000Z",
                    "uuid": f"assistant-uuid-{i+1}",
                    "sessionId": f"test-session-{i+1}"
                }
            ]
            
            with open(session_file, "w") as f:
                for item in test_data:
                    f.write(json.dumps(item) + "\n")
            
            session_files.append(session_file)
        
        output_dir = os.path.join(self.temp_dir, "bulk_export_test")
        
        # Test bulk export
        success = export_all_sessions_filtered(test_sessions_dir, output_dir)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_dir))
        
        # Check that files were created for each session
        output_files = os.listdir(output_dir)
        self.assertEqual(len(output_files), 3)
        
        # Check that all files have the _filtered_ suffix and .md extension
        for output_file in output_files:
            self.assertTrue(output_file.endswith('.md'))
            self.assertIn('_filtered_', output_file)
        
        # Check content of one of the files
        with open(os.path.join(output_dir, output_files[0]), 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("(Filtered)", content)
        self.assertIn("**Date**: 2025-01-15", content)

    def test_export_all_sessions_filtered_empty_directory(self):
        """Test bulk export with empty directory"""
        empty_dir = os.path.join(self.temp_dir, "empty_sessions")
        os.makedirs(empty_dir)
        
        output_dir = os.path.join(self.temp_dir, "empty_export_test")
        
        # Should succeed but with no files processed
        success = export_all_sessions_filtered(empty_dir, output_dir)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(output_dir))
        
        # Output directory should be empty
        output_files = os.listdir(output_dir)
        self.assertEqual(len(output_files), 0)

    def test_export_all_sessions_filtered_nonexistent_directory(self):
        """Test bulk export with non-existent directory"""
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        output_dir = os.path.join(self.temp_dir, "nonexistent_export_test")
        
        # Should fail
        success = export_all_sessions_filtered(nonexistent_dir, output_dir)
        self.assertFalse(success)

    def test_export_all_sessions_filtered_with_invalid_files(self):
        """Test bulk export with mix of valid and invalid session files"""
        test_sessions_dir = os.path.join(self.temp_dir, "mixed_sessions")
        os.makedirs(test_sessions_dir)
        
        # Create one valid session file
        valid_session = os.path.join(test_sessions_dir, "valid_session.jsonl")
        test_data = [
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": "Valid session"
                },
                "timestamp": "2025-01-15T10:30:00.000Z",
                "uuid": "user-uuid-1",
                "sessionId": "valid-session"
            }
        ]
        
        with open(valid_session, "w") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")
        
        # Create an invalid session file (empty)
        invalid_session = os.path.join(test_sessions_dir, "invalid_session.jsonl")
        with open(invalid_session, "w") as f:
            f.write("")  # Empty file
        
        # Create another invalid file (malformed JSON)
        malformed_session = os.path.join(test_sessions_dir, "malformed_session.jsonl")
        with open(malformed_session, "w") as f:
            f.write("not json\n")
        
        output_dir = os.path.join(self.temp_dir, "mixed_export_test")
        
        # Should succeed but only process the valid file
        success = export_all_sessions_filtered(test_sessions_dir, output_dir)
        self.assertTrue(success)
        
        # Should only have one output file (from the valid session)
        output_files = os.listdir(output_dir)
        self.assertEqual(len(output_files), 1)
        self.assertIn("valid_session", output_files[0])


if __name__ == "__main__":
    unittest.main()