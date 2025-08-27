#!/usr/bin/env python3

import json
import os
import tempfile
import unittest
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cclog_helper import export_markdown, format_markdown_message


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


if __name__ == "__main__":
    unittest.main()