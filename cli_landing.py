#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Bridge - Native CLI Landing Page
A terminal interface matching the LMBRIDGE v1.0.0 design
"""

import sys
import os
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ANSI Color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Specific colors from image
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;141m'
    GRAY = '\033[38;5;245m'


# Box drawing characters
class BoxChars:
    # Single line
    TL = '╭'
    TR = '╮'
    BL = '╰'
    BR = '╯'
    H = '─'
    V = '│'
    # Double line
    DTL = '╔'
    DTR = '╗'
    DBL = '╚'
    DBR = '╝'
    DH = '═'
    DV = '║'
    # T junctions
    TD = '┬'
    TU = '┴'
    TL_R = '├'
    TR_L = '┤'
    # Cross
    CROSS = '┼'


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the LMBRIDGE header with Unicode box drawing."""
    width = 58

    print(Colors.ORANGE + Colors.BOLD + '╭' + '─' * width + '╮' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + ' ' * width + Colors.ORANGE + '│' + Colors.RESET)

    # Title
    title = 'LMBRIDGE'
    version = 'v1.0.0'
    padding = width - len(title) - len(version) - 1

    print(Colors.ORANGE + '│' + Colors.RESET +
          Colors.BOLD + Colors.ORANGE + ' ' + title + Colors.RESET +
          ' ' * padding +
          Colors.DIM + version + Colors.RESET +
          Colors.ORANGE + ' │' + Colors.RESET)

    print(Colors.ORANGE + '│' + Colors.RESET + ' ' * width + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '╰' + '─' * width + '╯' + Colors.RESET)


def print_robot():
    """Print the ASCII robot mascot."""
    robot = f'''{Colors.PURPLE}
          ╱───────────────╲
         ╱                 ╲
        │                   │
        │    ╭─────────╮    │
        │    │ ⬤    ⬤ │    │
        │    │    ∩    │    │
        │    │  ────   │    │
        │    │  ⎛ ⎞   │    │
        │    │  ⎝ ⎠   │    │
        │    ╰─────────╯    │
        │         │         │
        │        ╱ ╲        │
        │       │   │       │
        │      ──────      │
        │     ╱───────╲     │
        │    ╱         ╲    │
        │   │           │   │
        │   │           │   │
        │    ╲         ╱    │
        │     ╲───────╱     │
        │      │     │      │
        │      │     │      │
        ╲───────┴─────┴──────╱
         ╲─────────────────╱
          ╲_______________╱
{Colors.RESET}'''
    print(robot)


def print_welcome():
    """Print welcome message."""
    print()
    print(Colors.WHITE + '    Welcome to ' + Colors.ORANGE + Colors.BOLD + 'LMBRIDGE' + Colors.RESET +
          Colors.WHITE + ' — ' + Colors.DIM + 'Local Model Terminal Bridge' + Colors.RESET)
    print()


def print_activity_box():
    """Print the Recent Activity box."""
    width = 50

    print(Colors.ORANGE + '┌' + '─' * width + '┐' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + Colors.BOLD + Colors.ORANGE + '  Recent Activity' +
          Colors.RESET + ' ' * (width - 18) + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + ' ' * width + Colors.ORANGE + '│' + Colors.RESET)

    activities = [
        ('Bridge initialized', '1m ago'),
        ('Connected to LM Studio API', '4m ago'),
        ('Tool registry loaded', '6m ago'),
        ('PowerShell command executed', '9m ago'),
        ('Security policy updated', '1h ago'),
    ]

    for action, time in activities:
        padding = width - len(action) - len(time) - 4
        print(Colors.ORANGE + '│' + Colors.RESET + '  ' + Colors.WHITE + action + Colors.RESET +
              ' ' * padding + Colors.GRAY + time + Colors.RESET + '  ' + Colors.ORANGE + '│' + Colors.RESET)

    print(Colors.ORANGE + '│' + Colors.RESET + ' ' * width + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + Colors.DIM + '  ... /resume for more' +
          Colors.RESET + ' ' * (width - 20) + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '└' + '─' * width + '┘' + Colors.RESET)


def print_features_box():
    """Print the What's New box."""
    width = 50

    print(Colors.ORANGE + '┌' + '─' * width + '┐' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + Colors.BOLD + Colors.ORANGE + "  What's New" +
          Colors.RESET + ' ' * (width - 13) + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + ' ' * width + Colors.ORANGE + '│' + Colors.RESET)

    features = [
        ('/agents', 'create autonomous command agents'),
        ('/terminal', 'direct terminal execution'),
        ('/security', 'inspect command sandbox'),
        ('ctrl+b', 'background shell sessions'),
        ('/tools', 'view tool registry'),
    ]

    for cmd, desc in features:
        padding = width - len(cmd) - len(desc) - 4
        print(Colors.ORANGE + '│' + Colors.RESET + '  ' + Colors.PURPLE + cmd + Colors.RESET +
              ' ' * padding + Colors.WHITE + desc + Colors.RESET + '  ' + Colors.ORANGE + '│' + Colors.RESET)

    print(Colors.ORANGE + '│' + Colors.RESET + ' ' * width + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '│' + Colors.RESET + Colors.DIM + '  ... /help for more' +
          Colors.RESET + ' ' * (width - 18) + Colors.ORANGE + '│' + Colors.RESET)
    print(Colors.ORANGE + '└' + '─' * width + '┘' + Colors.RESET)


def print_instructions():
    """Print command instructions."""
    print()
    print(Colors.GREEN + 'bridge>' + Colors.RESET + Colors.WHITE + ' Type /connect to attach to LM Studio' + Colors.RESET)
    print(Colors.GREEN + 'bridge>' + Colors.RESET + Colors.WHITE + ' Type /help to list commands' + Colors.RESET)
    print(Colors.GREEN + 'bridge>' + Colors.RESET + Colors.WHITE + ' Type /exit to quit' + Colors.RESET)
    print()


def print_full_landing():
    """Print the complete landing page."""
    clear_screen()

    # Top section
    print_header()

    # Two column layout approximation
    print()
    print('    ' + Colors.ORANGE + '╭' + '─' * 26 + '╮' + Colors.RESET + '    ' + Colors.ORANGE + '┌' + '─' * 50 + '┐' + Colors.RESET)
    print('    ' + Colors.ORANGE + '│' + Colors.RESET + ' ' * 26 + Colors.ORANGE + '│' + Colors.RESET + '    ' + Colors.ORANGE + '│' + Colors.RESET + Colors.BOLD + Colors.ORANGE + '  Recent Activity' + Colors.RESET + ' ' * 34 + Colors.ORANGE + '│' + Colors.RESET)

    # Robot on left, activity start on right
    robot_lines = [
        ('          ╱───────────────╲    ', '  Bridge initialized                     1m ago'),
        ('         ╱                 ╲   ', '  Connected to LM Studio API            4m ago'),
        ('        │                   │  ', '  Tool registry loaded                   6m ago'),
        ('        │    ╭─────────╮    │  ', '  PowerShell command executed            9m ago'),
        ('        │    │ ⬤    ⬤ │    │  ', '  Security policy updated                1h ago'),
        ('        │    │    ∩    │    │  ', '                                         '),
        ('        │    │  ────   │    │  ', '  ... /resume for more                   '),
        ('        │    │  ⎛ ⎞   │    │  ', '                                         '),
        ('        │    │  ⎝ ⎠   │    │  ', '                                         '),
        ('        │    ╰─────────╯    │  ', '                                         '),
        ('        │         │         │  ', '                                         '),
        ('        │        ╱ ╲        │  ', '                                         '),
        ('        │       │   │       │  ', '                                         '),
        ('        │      ──────      │  ', '                                         '),
        ('        │     ╱───────╲     │  ', '                                         '),
        ('        │    ╱         ╲    │  ', '                                         '),
        ('        │   │           │   │  ', '                                         '),
        ('        │   │           │   │  ', '                                         '),
        ('        │    ╲         ╱    │  ', '                                         '),
        ('        │     ╲───────╱     │  ', '                                         '),
        ('        │      │     │      │  ', '                                         '),
        ('        │      │     │      │  ', '                                         '),
        ('        ╲───────┴─────┴──────╱  ', '                                         '),
        ('         ╲─────────────────╱   ', '                                         '),
        ('          ╲_______________╱    ', '                                         '),
    ]

    for robot_line, empty in robot_lines:
        print('    ' + Colors.ORANGE + '│' + Colors.RESET + Colors.PURPLE + robot_line + Colors.RESET + Colors.ORANGE + '│' + Colors.RESET + '    ' + Colors.ORANGE + '│' + Colors.RESET + empty + Colors.ORANGE + '│' + Colors.RESET)

    print('    ' + Colors.ORANGE + '╰' + '─' * 26 + '╯' + Colors.RESET + '    ' + Colors.ORANGE + '└' + '─' * 50 + '┘' + Colors.RESET)

    # Features box
    print('    ' + ' ' * 28 + Colors.ORANGE + '┌' + '─' * 50 + '┐' + Colors.RESET)
    print('    ' + ' ' * 28 + Colors.ORANGE + '│' + Colors.RESET + Colors.BOLD + Colors.ORANGE + "  What's New" + Colors.RESET + ' ' * 39 + Colors.ORANGE + '│' + Colors.RESET)

    features = [
        ('/agents', 'create autonomous command agents'),
        ('/terminal', 'direct terminal execution'),
        ('/security', 'inspect command sandbox'),
        ('ctrl+b', 'background shell sessions'),
        ('/tools', 'view tool registry'),
    ]

    for cmd, desc in features:
        padding = 50 - len(cmd) - len(desc) - 4
        print('    ' + ' ' * 28 + Colors.ORANGE + '│' + Colors.RESET + '  ' + Colors.PURPLE + cmd + Colors.RESET + ' ' * padding + Colors.WHITE + desc + Colors.RESET + '  ' + Colors.ORANGE + '│' + Colors.RESET)

    print('    ' + ' ' * 28 + Colors.ORANGE + '│' + Colors.RESET + ' ' * 50 + Colors.ORANGE + '│' + Colors.RESET)
    print('    ' + ' ' * 28 + Colors.ORANGE + '│' + Colors.RESET + Colors.DIM + '  ... /help for more' + Colors.RESET + ' ' * 33 + Colors.ORANGE + '│' + Colors.RESET)
    print('    ' + ' ' * 28 + Colors.ORANGE + '└' + '─' * 50 + '┘' + Colors.RESET)

    print()
    print(Colors.WHITE + '    Welcome to ' + Colors.ORANGE + Colors.BOLD + 'LMBRIDGE' + Colors.RESET + Colors.WHITE + ' — ' + Colors.DIM + 'Local Model Terminal Bridge' + Colors.RESET)
    print()
    print()
    print(Colors.GREEN + 'bridge>' + Colors.RESET + Colors.WHITE + ' Type /connect to attach to LM Studio' + Colors.RESET)
    print(Colors.GREEN + 'bridge>' + Colors.RESET + Colors.WHITE + ' Type /help to list commands' + Colors.RESET)
    print(Colors.GREEN + 'bridge>' + Colors.RESET + Colors.WHITE + ' Type /exit to quit' + Colors.RESET)
    print()


def main():
    """Main entry point."""
    print_full_landing()

    # Simple command loop
    while True:
        try:
            cmd = input(Colors.GREEN + 'bridge>' + Colors.RESET + ' ').strip()

            if not cmd:
                continue

            if cmd.lower() in ['/exit', 'quit', 'q']:
                print(Colors.YELLOW + 'Goodbye!' + Colors.RESET)
                break
            elif cmd == '/help':
                print(Colors.ORANGE + 'Available commands:' + Colors.RESET)
                print('  /connect  - Connect to LM Studio')
                print('  /agents   - Create autonomous agents')
                print('  /terminal - Direct terminal execution')
                print('  /security - Inspect command sandbox')
                print('  /tools    - View tool registry')
                print('  /resume   - View more activity')
                print('  /exit     - Exit bridge')
                print()
            elif cmd == '/connect':
                print(Colors.GREEN + '✓' + Colors.RESET + Colors.WHITE + ' Connecting to LM Studio at http://127.0.0.1:1234/v1' + Colors.RESET)
                print(Colors.DIM + '  Use "ask: <prompt>" to send queries to the model' + Colors.RESET)
                print()
            elif cmd.startswith('ask:'):
                prompt = cmd[4:].strip()
                if prompt:
                    print(Colors.CYAN + '🤖 Thinking...' + Colors.RESET)
                    print(Colors.DIM + '  (Bridge to LM Studio - Model response would appear here)' + Colors.RESET)
                print()
            else:
                print(Colors.GRAY + f'Unknown command: {cmd}' + Colors.RESET)
                print(Colors.DIM + 'Type /help for available commands' + Colors.RESET)
                print()

        except KeyboardInterrupt:
            print()
            print(Colors.YELLOW + 'Use /exit to quit' + Colors.RESET)
        except EOFError:
            break


if __name__ == '__main__':
    main()
