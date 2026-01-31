# Project Manager

A desktop application for organizing and managing your programming projects. Built with Python and PyQt6.

![Project Manager Screenshot](screenshot.png)

## Features

- **Project Discovery** - Automatically scans directories to find programming projects
- **Language Detection** - Identifies programming languages used in each project
- **Grid & List Views** - Switch between visual card layout and compact table view
- **Status Tracking** - Mark projects as Active, On Hold, or Archived
- **Favorites** - Star important projects for quick access
- **Quick Actions** - Open projects in file explorer, terminal, or Claude Code
- **Custom Commands** - Define per-project commands (build, test, deploy) accessible from the context menu
- **Search & Filter** - Find projects by name, filter by status or language
- **Batch Operations** - Select multiple projects to change status at once

## Installation

### Download

Download the latest `ProjectManager.exe` from the [Releases](../../releases) page.

### Build from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/KaldarAralay/projectManager.git
   cd projectManager
   ```

2. Install dependencies:
   ```bash
   pip install PyQt6
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. (Optional) Build executable:
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --noconsole --icon=project-manager-icon.ico --name=ProjectManager main.py
   ```

## Usage

### Getting Started

1. Open the application
2. Click the **Settings** (gear icon) to configure scan directories
3. Add folders where your projects are stored
4. Click **Refresh** to scan for projects

### Custom Commands

Define custom commands for each project that appear in the right-click context menu:

1. Right-click a project and select **Edit Details**
2. Scroll to the **Custom Commands** section
3. Click **Add** to create a new command
4. Enter a name (e.g., "Build") and command (e.g., "npm run build")
5. Save and right-click the project to run your command

**Placeholders:**
- `{path}` - Project directory path
- `{name}` - Project name

**Examples:**
| Name | Command |
|------|---------|
| Build | `npm run build` |
| Test | `pytest` |
| Dev Server | `npm run dev` |
| Open in VS Code | `code {path}` |

## Project Structure

```
projectManager/
├── main.py                 # Application entry point
├── src/
│   ├── app.py              # Application controller
│   ├── database.py         # SQLite database handler
│   ├── scanner.py          # Project directory scanner
│   ├── models/
│   │   └── project.py      # Project data model
│   ├── ui/
│   │   ├── main_window.py  # Main application window
│   │   ├── toolbar.py      # Top toolbar
│   │   ├── sidebar.py      # Filter sidebar
│   │   ├── project_card.py # Grid view card widget
│   │   ├── project_list.py # List view table widget
│   │   └── dialogs/        # Dialog windows
│   └── utils/
│       ├── theme.py        # Color theme definitions
│       └── detector.py     # Language detection
└── tests/                  # Unit tests
```

## Configuration

Data is stored in `~/.projectmanager/`:
- `projects.db` - SQLite database with project metadata

## Requirements

- Python 3.10+
- PyQt6

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
