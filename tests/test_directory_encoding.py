#!/usr/bin/env python3
"""Tests for directory encoding logic used in cclog.sh"""

import subprocess
import pytest
import os


def encode_directory_path(path):
    """
    Python implementation of the bash directory encoding logic:
    sed 's/\//-/g; s/\./-/g; s/_/-/g'
    """
    return path.replace('/', '-').replace('.', '-').replace('_', '-')


def bash_encode_directory_path(path):
    """
    Call the actual bash command to encode directory path
    """
    try:
        result = subprocess.run(
            ['bash', '-c', f'echo "{path}" | sed "s/\\//-/g; s/\\./-/g; s/_/-/g"'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Bash command failed: {e}")


class TestDirectoryEncoding:
    """Tests for directory path encoding used by cclog export-all-filtered"""

    def test_basic_path_encoding(self):
        """Test basic directory path encoding"""
        test_cases = [
            ("/Users/username/project", "-Users-username-project"),
            ("/home/user/my-app", "-home-user-my-app"),
            (".", "-"),
            ("/", "-"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected

    def test_underscore_encoding(self):
        """Test that underscores are properly encoded (the bug we fixed)"""
        test_cases = [
            ("/Users/user/my_project", "-Users-user-my-project"),
            ("/dev/eos/eneos_ev_app", "-dev-eos-eneos-ev-app"),
            ("my_test_app", "my-test-app"),
            ("_underscore_start", "-underscore-start"),
            ("end_underscore_", "end-underscore-"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected

    def test_dot_encoding(self):
        """Test that dots are properly encoded"""
        test_cases = [
            ("/Users/user/.hidden", "-Users-user--hidden"),
            ("app.config.js", "app-config-js"),
            ("...dots", "---dots"),
            (".env.local", "-env-local"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected

    def test_mixed_special_characters(self):
        """Test paths with multiple types of special characters"""
        test_cases = [
            ("/Users/user/my_app.config", "-Users-user-my-app-config"),
            ("/home/.local/my_project", "-home--local-my-project"),
            ("./app_config/test.env", "--app-config-test-env"),
            ("/path/with.dots_and/slashes", "-path-with-dots-and-slashes"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected

    def test_consecutive_special_characters(self):
        """Test paths with consecutive special characters"""
        test_cases = [
            ("//double//slash", "--double--slash"),
            ("..double..dot", "--double--dot"),
            ("__double__underscore", "--double--underscore"),
            ("/._mixed_./", "---mixed---"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected

    def test_real_world_examples(self):
        """Test with real-world project paths"""
        test_cases = [
            # The original bug case
            ("/Users/yutakatada/dev/eos/eneos_ev_app", "-Users-yutakatada-dev-eos-eneos-ev-app"),
            # Common project structures
            ("/Users/developer/workspace/my-react-app", "-Users-developer-workspace-my-react-app"),
            ("/home/user/projects/django_project", "-home-user-projects-django-project"),
            ("/var/www/node_app.production", "-var-www-node-app-production"),
            ("C:\\Users\\user\\my_project", "C:\\Users\\user\\my-project"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected

    def test_empty_and_edge_cases(self):
        """Test edge cases like empty strings and single characters"""
        test_cases = [
            ("", ""),
            ("a", "a"),
            ("_", "-"),
            (".", "-"),
            ("/", "-"),
            ("/_./", "----"),
        ]
        
        for input_path, expected in test_cases:
            assert encode_directory_path(input_path) == expected
            assert bash_encode_directory_path(input_path) == expected