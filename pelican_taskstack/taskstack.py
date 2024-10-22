import os
import re
from datetime import datetime, timedelta
from github3 import login
from pelican import signals
from jinja2 import Template

class TaskStack:
    def __init__(self, pelican):
        self.pelican = pelican
        self.settings = pelican.settings
        self.github_token = self._get_github_token()
        self.pomodoro_duration = self.settings.get('TASKSTACK_POMODORO_DURATION', 25)
        self.use_template = self.settings.get('TASKSTACK_USE_TEMPLATE', False)
        self._init_github()

    def _get_github_token(self):
        """Get GitHub token from environment or settings."""
        return os.environ.get('GITHUB_TOKEN') or self.settings.get('GITHUB_TOKEN')

    def _get_repository_from_git(self):
        """Extract repository info from git remote URL."""
        try:
            # Try to read git config
            with open('.git/config', 'r') as f:
                config = f.read()
            
            # Look for GitHub remote URL
            patterns = [
                r'git@github\.com:(.+?/.+?)\.git',  # SSH format
                r'https://github\.com/(.+?/.+?)\.git',  # HTTPS format
                r'https://github\.com/(.+?/.+?)(?:\.git)?$'  # HTTPS without .git
            ]
            
            for pattern in patterns:
                match = re.search(pattern, config)
                if match:
                    return match.group(1)
            
            return None
        except:
            return None

    def _get_repository_from_env(self):
        """Get repository from GitHub Actions environment."""
        if 'GITHUB_REPOSITORY' in os.environ:
            return os.environ['GITHUB_REPOSITORY']
        return None

    def _init_github(self):
        """Initialize GitHub connection."""
        if not self.github_token:
            raise ValueError("GitHub token not found in environment or settings")

        # Try to get repository information from different sources
        repo_full_name = (
            self.settings.get('GITHUB_REPOSITORY') or  # From pelican settings
            self._get_repository_from_env() or         # From GitHub Actions
            self._get_repository_from_git()            # From git config
        )

        if not repo_full_name:
            raise ValueError("Could not determine GitHub repository")

        self.gh = login(token=self.github_token)
        owner, repo = repo_full_name.split('/')
        self.repo = self.gh.repository(owner, repo)

    def inject_content(self, content):
        """Inject taskstack content into an article or page."""
        if '{taskstack}' in content._content:
            tasks = self.get_tasks()
            
            # Generate HTML content
            tasks_html = self._generate_tasks_html(tasks)
            
            # Inject CSS and JS
            css = self._get_static_content('css/taskstack.css')
            js = self._get_static_content('js/taskstack.js')
            
            # Replace placeholder with content and add CSS/JS
            content._content = content._content.replace(
                '{taskstack}',
                f'<style>{css}</style>\n{tasks_html}\n<script>{js}</script>'
            )

    def _get_static_content(self, filename):
        """Read static file content."""
        static_path = os.path.join(os.path.dirname(__file__), 'static', filename)
        with open(static_path, 'r') as f:
            return f.read()

    def _generate_tasks_html(self, tasks):
        """Generate HTML for tasks without using a template file."""
        html = ['<div class="taskstack">']
        
        # Stacked tasks
        html.append('<div class="stacked-tasks">')
        html.append('<h2>Task Pipeline</h2>')
        for task in tasks['stacked']:
            html.append(f'''
                <div class="task">
                    <a href="{task['url']}">{task['number']} {task['title']}</a>
                    <div class="pomodoro-count">
                        🍅 × {len(task['pomodoros'])}
                    </div>
                </div>
            ''')
        html.append('</div>')
        
        # Active task
        if tasks['active']:
            html.append('<div class="active-task">')
            html.append('<h2>Current Task</h2>')
            task = tasks['active']
            progress = task.get('current_pomodoro', 0)
            html.append(f'''
                <div class="task">
                    <a href="{task['url']}">{task['number']} {task['title']}</a>
                    <div class="progress-bar" data-duration="{self.pomodoro_duration}" 
                         data-progress="{progress}">
                        <div class="progress"></div>
                    </div>
                </div>
            ''')
            html.append('</div>')
        
        # Today's tasks
        if tasks['today']:
            html.append('<div class="today-tasks">')
            html.append('<h2>Completed Today</h2>')
            for task in tasks['today']:
                html.append(f'''
                    <div class="task">
                        <a href="{task['url']}">{task['number']} {task['title']}</a>
                        <div class="pomodoro-count">
                            🍅 × {len(task['pomodoros'])}
                        </div>
                    </div>
                ''')
            html.append('</div>')
        
        html.append('</div>')
        return '\n'.join(html)

    def generate_output(self, writer):
        """Generate output file only if template mode is enabled."""
        if not self.use_template:
            return
            
        tasks = self.get_tasks()
        
        # Load template
        template_path = os.path.join(os.path.dirname(__file__), 'templates/taskstack.html')
        with open(template_path) as f:
            template = Template(f.read())

        # Generate HTML
        content = template.render(
            tasks=tasks,
            pomodoro_duration=self.pomodoro_duration
        )

        # Write output
        output_path = os.path.join(self.settings['OUTPUT_PATH'], 'taskstack.html')
        with open(output_path, 'w') as f:
            f.write(content)

        if self.use_template:
            self._copy_static_files(writer)

