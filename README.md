# Pelican TaskStack Plugin

A Pelican plugin that visualizes your GitHub issues as a task stack, with support for pomodoro tracking and progress visualization. It integrates with GitHub's issue system to show stacked tasks, active tasks, and work progress using labels.

## Features

- 📚 Displays stacked tasks from GitHub issues
- ⏱️ Shows active pomodoro sessions with real-time progress
- 📊 Tracks work done today
- 🏷️ Uses GitHub labels for task management
- 🔄 Auto-updates progress via JavaScript
- 🌙 Supports light/dark mode
- 🔌 Easy integration with GitHub Actions
- 📱 Responsive design

## Installation

Install directly from GitHub:
```bash
pip install git+https://github.com/DiosDelRayo/pelican-taskstack
```

Or install from source:
```bash
git clone https://github.com/DiosDelRayo/pelican-taskstack.git
cd pelican-taskstack
pip install -e .
```

## Usage

### Basic Setup

1. Add the plugin to your `pelicanconf.py`:
```python
PLUGINS = ['pelican_taskstack']
```

2. Insert the taskstack visualization in your content:
```markdown
# My Tasks

Current progress:

{taskstack}
```

### GitHub Setup

1. Create labels in your repository:
   - `Stacked`: For tasks in the pipeline
   - `Active`: For the current/next task
   - `WIP`: For tasks currently being worked on

2. Apply labels to your issues:
   - Mark upcoming tasks with `Stacked`
   - Mark your current focus with `Active`
   - Toggle `WIP` when starting/stopping work sessions

## Detailed Configuration

### Basic Configuration
```python
# pelicanconf.py

# GitHub Authentication (Required)
GITHUB_TOKEN = 'your-token-here'  # Alternative: use environment variable

# Repository Settings (Optional)
GITHUB_REPOSITORY = 'owner/repo'  # Auto-detected if not specified
GITHUB_API_URL = 'https://api.github.com'  # For GitHub Enterprise

# Pomodoro Settings
TASKSTACK_POMODORO_DURATION = 25  # Duration in minutes (default: 25)
TASKSTACK_BREAK_DURATION = 5      # Break duration in minutes (default: 5)
TASKSTACK_LONG_BREAK_DURATION = 15  # Long break duration (default: 15)
TASKSTACK_POMODOROS_BEFORE_BREAK = 4  # Pomodoros before long break (default: 4)

# Display Settings
TASKSTACK_USE_TEMPLATE = False    # Use separate template (default: False)
TASKSTACK_SHOW_COMPLETED = True   # Show completed tasks (default: True)
TASKSTACK_MAX_STACKED = 10        # Maximum stacked tasks to show (default: 10)
TASKSTACK_DATE_FORMAT = '%Y-%m-%d %H:%M'  # Date format (default: '%Y-%m-%d %H:%M')

# Custom Label Names (Optional)
TASKSTACK_LABELS = {
    'stacked': 'Stacked',
    'active': 'Active',
    'wip': 'WIP'
}

# Progress Bar Settings
TASKSTACK_PROGRESS_ANIMATION = True  # Enable progress animation (default: True)
TASKSTACK_UPDATE_INTERVAL = 1000     # Update interval in ms (default: 1000)
```

### Environment Variables

Local development or CI:
```bash
export GITHUB_TOKEN=your-token-here
export GITHUB_REPOSITORY=owner/repo  # Optional
```

### GitHub Actions Integration

```yaml
name: Build and Deploy
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build website
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: pelican content -s publishconf.py
```

## Customizing Styles

### Basic CSS Overrides

Create a `custom.css` in your theme:

```css
/* Customize task cards */
.taskstack .task {
    border-radius: 8px;
    padding: 15px;
    margin: 12px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Customize progress bar */
.taskstack .progress-bar {
    height: 8px;
    border-radius: 4px;
    background-color: #eee;
}

.taskstack .progress {
    background: linear-gradient(90deg, #4CAF50, #81C784);
    border-radius: 4px;
}

/* Custom dark mode */
@media (prefers-color-scheme: dark) {
    .taskstack .task {
        background-color: #2d2d2d;
        border-color: #404040;
    }
    
    .taskstack .progress-bar {
        background-color: #404040;
    }
}
```

### Advanced Styling

#### Custom Component Classes
```css
/* Task status indicators */
.taskstack .task[data-status="active"] {
    border-left: 4px solid #4CAF50;
}

.taskstack .task[data-status="stacked"] {
    border-left: 4px solid #2196F3;
}

/* Custom animations */
.taskstack .progress {
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}

.taskstack .task:hover {
    animation: pulse 1s infinite;
}
```

#### Layout Customization
```css
/* Grid layout for larger screens */
@media (min-width: 768px) {
    .taskstack {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 20px;
    }
    
    .taskstack .stacked-tasks {
        grid-column: 1;
    }
    
    .taskstack .active-task,
    .taskstack .today-tasks {
        grid-column: 2;
    }
}
```

### JavaScript Customization

Create a `custom.js` in your theme:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Custom progress bar behavior
    const progressBars = document.querySelectorAll('.taskstack .progress-bar');
    progressBars.forEach(bar => {
        // Add custom click handler
        bar.addEventListener('click', function() {
            // Your custom logic
        });
    });
    
    // Custom task card interactions
    const tasks = document.querySelectorAll('.taskstack .task');
    tasks.forEach(task => {
        task.addEventListener('click', function() {
            // Your custom logic
        });
    });
});
```

## Development

### Running Tests
```bash
python setup.py test
```

### Local Development
```bash
export GITHUB_TOKEN=your-token-here
pelican content
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is released under the [BipCot NoGov License](https://bipcot.org/).

The BipCot NoGov License is an open source license that prohibits use by governments and their agents.

For the full license text, see the [license](LICENSE.md) file in the repository.

## Acknowledgments

- Built for Pelican Static Site Generator
- Uses github3.py for GitHub API integration
- Inspired by pomodoro technique and kanban boards
