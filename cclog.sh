#!/bin/bash
# cclog - Browse Claude Code conversation history with fzf

# Get the full path to this script at the top level
CCLOG_SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
# Resolve to absolute path
if [[ ! "$CCLOG_SCRIPT_PATH" =~ ^/ ]]; then
    CCLOG_SCRIPT_PATH="$(cd "$(dirname "$CCLOG_SCRIPT_PATH")" && pwd)/$(basename "$CCLOG_SCRIPT_PATH")"
fi

# Find Python executable once
CCLOG_PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    CCLOG_PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    # Check if it's Python 3
    if python -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)" 2>/dev/null; then
        CCLOG_PYTHON="python"
    fi
fi

# Get the helper script path
CCLOG_HELPER_SCRIPT="$(dirname "$CCLOG_SCRIPT_PATH")/cclog_helper.py"

# Function to format Claude Code chat logs with colors (internal use)
__cclog_view() {
    if [ $# -eq 0 ]; then
        echo "Error: view requires a file argument" >&2
        return 1
    fi

    local file="$1"

    # Use Python helper if available
    if [ -f "$CCLOG_HELPER_SCRIPT" ] && [ -n "$CCLOG_PYTHON" ]; then
        "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" view "$file"
    else
        echo "Error: Python 3 is required for view" >&2
        return 1
    fi
}

# Function to format duration from seconds
__cclog_format_duration() {
    local duration=$1

    if [ "$duration" -lt 60 ]; then
        echo "${duration}s"
    elif [ "$duration" -lt 3600 ]; then
        echo "$((duration / 60))m"
    elif [ "$duration" -lt 86400 ]; then
        local hours=$((duration / 3600))
        local minutes=$(((duration % 3600) / 60))
        if [ "$minutes" -gt 0 ]; then
            echo "${hours}h ${minutes}m"
        else
            echo "${hours}h"
        fi
    else
        local days=$((duration / 86400))
        local hours=$(((duration % 86400) / 3600))
        if [ "$hours" -gt 0 ]; then
            echo "${days}d ${hours}h"
        else
            echo "${days}d"
        fi
    fi
}

# Function to generate session list (internal)
__cclog_generate_list() {
    local claude_projects_dir="$1"

    # Use Python helper if available
    if [ -f "$CCLOG_HELPER_SCRIPT" ] && [ -n "$CCLOG_PYTHON" ]; then
        # Pass terminal columns to the helper
        # Try multiple methods to get terminal width:
        # 1. Use existing COLUMNS if set
        # 2. Try tput cols
        # 3. Try stty size
        # 4. Default to 80
        if [ -z "$COLUMNS" ]; then
            COLUMNS=$(tput cols 2>/dev/null || stty size 2>/dev/null | cut -d' ' -f2 || echo 80)
        fi
        COLUMNS="$COLUMNS" "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" list "$claude_projects_dir"
    else
        echo "Error: Python 3 is required for cclog" >&2
        return 1
    fi
}

# Function to show session info (internal use)
__cclog_info() {
    if [ $# -eq 0 ]; then
        echo "Error: info requires a file argument" >&2
        return 1
    fi

    local file="$1"

    # Use Python helper if available
    if [ -f "$CCLOG_HELPER_SCRIPT" ] && [ -n "$CCLOG_PYTHON" ]; then
        "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" info "$file"
    else
        echo "Error: Python 3 is required for info" >&2
        return 1
    fi
}

# Function to browse logs with fzf (internal use)
__cclog_browse() {
    # If directory argument provided, use it; otherwise use current directory
    local target_dir="${1:-$(pwd)}"

    # Convert "/" to "-" and "." to "-" for project directory name
    local project_dir=$(echo "$target_dir" | sed 's/\//-/g; s/\./-/g')

    local claude_projects_dir="$HOME/.claude/projects/$project_dir"

    # Check if the directory exists
    if [ ! -d "$claude_projects_dir" ]; then
        echo "No Claude logs found for this project: $target_dir" >&2
        return 1
    fi

    # Create a simpler preview command using the Python helper directly
    local preview_cmd="$CCLOG_PYTHON $CCLOG_HELPER_SCRIPT info '$claude_projects_dir/{-1}.jsonl' && echo && $CCLOG_PYTHON $CCLOG_HELPER_SCRIPT view '$claude_projects_dir/{-1}.jsonl'"

    # Use fzf with formatted list - stream directly from function
    # Use Unit Separator (0x1F) as delimiter
    local result=$(__cclog_generate_list "$claude_projects_dir" | fzf \
        --header-lines=4 \
        --delimiter=$'\x1f' \
        --with-nth="1" \
        --preview "$preview_cmd" \
        --preview-window="down:60%:nowrap" \
        --height="100%" \
        --ansi \
        --bind "ctrl-r:execute(claude -r {-1})+abort" \
        --expect="ctrl-v,ctrl-p,ctrl-e,ctrl-f")

    # Process result
    if [ -n "$result" ]; then
        local key=$(echo "$result" | head -1)
        # Get everything after first line, but treat it as one selection
        local selected=$(echo "$result" | tail -n +2)

        if [ -n "$selected" ]; then
            # Extract session ID using Unit Separator delimiter
            local full_id=$(printf "%s" "$selected" | awk -F$'\x1f' 'END {print $NF}' | tr -d '\n')

            case "$key" in
            ctrl-v)
                # View the log
                local selected_file="$claude_projects_dir/${full_id}.jsonl"
                if [ -n "$PAGER" ]; then
                    __cclog_view "$selected_file" | $PAGER
                else
                    __cclog_view "$selected_file" | less -R
                fi
                ;;
            ctrl-p)
                # Return file path
                printf "%s\n" "$claude_projects_dir/${full_id}.jsonl"
                ;;
            ctrl-e)
                # Export to Markdown
                local selected_file="$claude_projects_dir/${full_id}.jsonl"
                if [ -f "$CCLOG_HELPER_SCRIPT" ] && [ -n "$CCLOG_PYTHON" ]; then
                    echo "Exporting session to Markdown..."
                    if "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" export "$selected_file" "claude_chat"; then
                        echo "Export completed successfully!"
                    else
                        echo "Export failed!" >&2
                    fi
                else
                    echo "Error: Python 3 is required for export" >&2
                fi
                ;;
            ctrl-f)
                # Export to Markdown with empty messages filtered
                local selected_file="$claude_projects_dir/${full_id}.jsonl"
                if [ -f "$CCLOG_HELPER_SCRIPT" ] && [ -n "$CCLOG_PYTHON" ]; then
                    echo "Exporting session to Markdown (filtered)..."
                    if "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" export-filtered "$selected_file" "claude_chat"; then
                        echo "Export (filtered) completed successfully!"
                    else
                        echo "Export failed!" >&2
                    fi
                else
                    echo "Error: Python 3 is required for export" >&2
                fi
                ;;
            *)
                # Default: return session ID
                printf "%s\n" "$full_id"
                ;;
            esac
        fi
    fi
}

# Function to browse all projects with fzf (internal use)
__cclog_projects() {
    # Check if we have the required tools
    if [ ! -f "$CCLOG_HELPER_SCRIPT" ] || [ -z "$CCLOG_PYTHON" ]; then
        echo "Error: Python 3 is required for projects" >&2
        return 1
    fi

    # Create preview command - show sessions for the selected project
    local preview_cmd="$CCLOG_PYTHON $CCLOG_HELPER_SCRIPT list '$HOME/.claude/projects/{-1}' | head -20"

    # Get terminal width for proper display
    if [ -z "$COLUMNS" ]; then
        COLUMNS=$(tput cols 2>/dev/null || stty size 2>/dev/null | cut -d' ' -f2 || echo 80)
    fi

    # Use fzf with project list
    local result=$(COLUMNS="$COLUMNS" "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" projects | fzf \
        --header-lines=3 \
        --delimiter=$'\x1f' \
        --with-nth="1" \
        --preview "$preview_cmd" \
        --preview-window="down:50%:nowrap" \
        --height="100%" \
        --ansi)

    # Process result
    if [ -n "$result" ]; then
        # Extract the encoded project name (after delimiter)
        local encoded_name=$(printf "%s" "$result" | awk -F$'\x1f' '{print $NF}' | tr -d '\n')

        if [ -n "$encoded_name" ]; then
            # Decode the project path
            local project_path=$("$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" decode "$encoded_name")
            if [ -n "$project_path" ]; then
                echo "cd $project_path"
                cd "$project_path"
            fi
        fi
    fi
}

# Main entry point for cclog command
cclog() {
    case "${1}" in
    projects | p)
        shift
        __cclog_projects "$@"
        ;;
    view | v)
        shift
        if [ -z "$1" ]; then
            echo "Usage: cclog view <session-file>" >&2
            return 1
        fi
        __cclog_view "$1"
        ;;
    info | i)
        shift
        if [ -z "$1" ]; then
            echo "Usage: cclog info <session-file>" >&2
            return 1
        fi
        __cclog_info "$1"
        ;;
    export-all-filtered | eaf)
        shift
        # Export all sessions in current project to filtered Markdown
        local target_dir="${1:-$(pwd)}"
        
        # Convert "/" to "-" and "." to "-" for project directory name
        local project_dir=$(echo "$target_dir" | sed 's/\//-/g; s/\./-/g')
        local claude_projects_dir="$HOME/.claude/projects/$project_dir"
        
        # Check if the directory exists
        if [ ! -d "$claude_projects_dir" ]; then
            echo "No Claude logs found for this project: $target_dir" >&2
            return 1
        fi
        
        # Use Python helper for bulk export
        if [ -f "$CCLOG_HELPER_SCRIPT" ] && [ -n "$CCLOG_PYTHON" ]; then
            echo "Exporting all sessions to Markdown (filtered)..."
            if "$CCLOG_PYTHON" "$CCLOG_HELPER_SCRIPT" export-all-filtered "$claude_projects_dir" "claude_chat"; then
                echo "Bulk export completed successfully!"
            else
                echo "Bulk export failed!" >&2
                return 1
            fi
        else
            echo "Error: Python 3 is required for bulk export" >&2
            return 1
        fi
        ;;
    help | h | --help | -h)
        cat <<EOF
cclog - Browse Claude Code conversation history

Usage:
    cclog [options]                   Browse sessions in current directory
    cclog projects                    Browse all projects
    cclog view <session>              View session content
    cclog info <session>              Show session information
    cclog export-all-filtered [dir]  Export all sessions to Markdown (filtered)
    cclog help                        Show this help message

Options:
    projects, p                       Browse all projects
    view, v                          View session content
    info, i                          Show session information
    export-all-filtered, eaf         Export all sessions to filtered Markdown
    help, h, --help, -h              Show help

Key bindings (in fzf browser):
    Enter: Return session ID, Ctrl-v: View log, Ctrl-p: Return path
    Ctrl-r: Resume conversation, Ctrl-e: Export to Markdown
    Ctrl-f: Export to Markdown (filtered)
EOF
        ;;
    *)
        # Default: browse current directory
        __cclog_browse "$@"
        ;;
    esac
}

# Execute the function if script is run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    cclog "$@"
fi
