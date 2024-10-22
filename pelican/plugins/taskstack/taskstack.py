import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from github3 import login
from pelican import signals
from jinja2 import Template
from pelican import signals
import logging

logger = logging.getLogger(__name__)
logger.warning('Load TaskStack')

class TaskStack:

    instance: 'TaskStack' = None

    def __init__(self, pelican):
        logger.warning(f'Create instance: {pelican}')
        self.pelican = pelican
        self.settings = pelican.settings
        self.github_token = self._get_github_token()
        self.pomodoro_duration = self.settings.get('TASKSTACK_POMODORO_DURATION', 25)
        self.use_template = self.settings.get('TASKSTACK_USE_TEMPLATE', False)
        self._init_github()

    def _get_github_token(self):
        """Get GitHub token from settings or environment."""
        return self.settings.get('GITHUB_TOKEN') or os.environ.get('GITHUB_TOKEN')

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
        self.owner, repo = repo_full_name.split('/')
        self.repo = self.gh.repository(self.owner, repo)

    def get_tasks(self):
        """Fetch and process GitHub issues."""
        tasks = {
            'stacked': [],
            'active': None,
            'wip': None
        }

        try:
            for issue in self.repo.issues():
                task = {
                    'title': issue.title,
                    'number': issue.number,
                    'url': issue.html_url,
                    'labels': [label.name for label in issue.labels],
                    'pomodoros': self._calculate_pomodoros(issue)
                }

                if 'Stacked' in task['labels']:
                    tasks['stacked'].append(task)
                if 'Active' in task['labels']:
                    tasks['active'] = task
                if 'WIP' in task['labels']:
                    tasks['wip'] = task
                    task['current_pomodoro'] = self._get_current_pomodoro_progress(issue)
        except e:
            logger.warning(f'Could not load tasks: {e})

        try:
            logger.information(f'tasks: {tasks}')
        except e:
            logger.warning(e)
        return tasks

    def _calculate_pomodoros(self, issue):
        """Calculate completed pomodoros from issue events."""
        pomodoros = []
        start_time = None

        for event in issue.events():
            if event.event == 'labeled' and event.label.name == 'WIP':
                start_time = event.created_at
            elif event.event == 'unlabeled' and event.label.name == 'WIP' and start_time:
                pomodoros.append({
                    'start': start_time,
                    'end': event.created_at,
                    'duration': (event.created_at - start_time).total_seconds() / 60
                })
                start_time = None

        return pomodoros

    def _get_current_pomodoro_progress(self, issue):
        """Calculate progress of current pomodoro."""
        for event in issue.events():
            if event.event == 'labeled' and event.label.name == 'WIP':
                start_time = event.created_at
                elapsed = (datetime.utcnow() - start_time).total_seconds() / 60
                return min(100, (elapsed / self.pomodoro_duration) * 100)
        return 0

    @classmethod
    def inject_content(cls, content):
        """Inject taskstack content into an article or page."""
        logger.warning(f'TaskStack.inject_content({content})')
        if not hasattr(content, '_content'):
            logger.warning('TaskStack.inject_content(): No content')
            return
        try:
            if '{taskstack}' in content._content:
                tasks = cls.instance.get_tasks()
                
                # Generate HTML content
                tasks_html = cls.instance._generate_tasks_html(tasks)
                
                # Inject CSS and JS
                css = cls.instance._get_static_content('css/taskstack.css')
                js = cls.instance._get_static_content('js/taskstack.js')
                
                # Replace placeholder with content and add CSS/JS
                content._content = content._content.replace(
                    '{taskstack}',
                    f'<style>{css}</style>\n{tasks_html}\n<script>{js}</script>'
                )
        except Exception as e:
            logger.warning(f"Error injecting taskstack content: {e}")
            # Don't fail completely, just show error message
            error_html = f'<div class="taskstack-error">Error loading taskstack: {str(e)}</div>'
            content._content = content._content.replace('{taskstack}', error_html)

    def _get_static_content(self, filename):
        """Read static file content."""
        static_path = Path(os.path.join(os.path.dirname(__file__), '../../', 'static', filename)).absolute()
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
        template_path = os.path.join(os.path.dirname(__file__), '../../templates/taskstack.html')
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

    @classmethod
    def initialize(cls, pelican) -> 'TaskStack':
        logger.warning(f'TaskStack.initialize({pelican})')
        cls.instance = cls(pelican)
        return cls.get_instance()

    @classmethod
    def get_instance(cls) -> 'TaskStack':
        return cls.instance


def register():
    """Register the plugin with Pelican."""
    logger.warning(f'register')

    def add_taskstack_to_context(generator, metadata):
        metadata['taskstack_instance'] = TaskStack.get_instance()

    signals.initialized.connect(TaskStack.initialize)
    signals.content_object_init.connect(TaskStack.inject_content)
    signals.page_generator_context.connect(add_taskstack_to_context)
    signals.article_generator_context.connect(add_taskstack_to_context)
