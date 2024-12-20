import os
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from github3 import login
from github3.issues.issue import ShortIssue
from pelican import signals
from jinja2 import Template
from pelican import signals
from math import ceil
from itertools import chain
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
        self.pomodoro_grace = self.settings.get('TASKSTACK_POMODORO_GRACE', 3)
        self.today_timespan = self.settings.get('TODAY_TIMESPAN', 24)
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
        if 'REPOSITORY' in os.environ:
            return os.environ['REPOSITORY']
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
            'today': [],
            'done': []
        }
        issues: list[ShortIssue] = []

        try:
            for issue in sorted(
                    chain(
                        self.repo.issues(state='all', since=(datetime.utcnow() - timedelta(hours=self.today_timespan))),
                        self.repo.issues(state='open', labels='Stacked'),
                    ),
                    key=lambda x: x.updated_at):
                logger.warning(type(issue))
                logger.warning(issue)
                if issue in issues:
                    continue
                issues.append(issue)
                task = {
                    'title': issue.title,
                    'number': issue.number,
                    'body': issue.body_html,
                    'url': issue.html_url,
                    'done': issue.is_closed(),
                    'stacked': False,
                    'active': False,
                    'wip': False,
                    'labels': [label.name for label in issue.labels()],
                    'pomodoros': self._calculate_pomodoros(issue)
                }

                if 'Active' in task['labels'] or 'WIP' in task['labels']:
                    task['active'] = True
                    tasks['active'] = task
                    continue
                if 'Stacked' in task['labels'] and not task['done']:
                    task['stacked'] = True
                    tasks['stacked'].append(task)
                    continue
                #if not self._has_pomodoros_today(task):
                #    continue
                if len(task['pomodoros']) > 0 and not task['done']:
                    tasks['today'].append(task)
                    continue
                if len(task['pomodoros']) > 0 and task['done']:
                    tasks['done'].append(task)
        except Exception as e:
            logger.warning(f'Could not load tasks: {e}')

        try:
            logger.info(f'tasks: {tasks}')
        except Exception as e:
            logger.warning(e)
        return tasks

    def _has_pomodoros_today(self, task: list) -> bool:
        for pomodoro in issues['pomodoros']:
            if pomodoro['today']:
                return True
        return False

    def _calculate_pomodoros(self, issue: ShortIssue) -> list:
        """Calculate completed pomodoros from issue events."""
        today_start = (datetime.utcnow() - timedelta(hours=self.today_timespan)).astimezone(timezone.utc)
        pomodoros = []
        start_time = None

        try:
            pomodoro = None
            for event in issue.events():
                logger.warning(type(event))
                if event.event == 'labeled' and event.label['name'] == 'WIP':
                    if pomodoro:
                        pomodoros.append(pomodoro)
                    start_time = event.created_at
                    pomodoro = {
                        'start': start_time,
                        'end': None,
                        'duration': None,
                        'progress': None,
                        'overflow': False,
                        'today': start_time > today_start
                    }
                elif event.event == 'unlabeled' and event.label['name'] == 'WIP' and start_time:
                    duration = ceil(((event.created_at - start_time).total_seconds() / 60))
                    pomodoro['end'] = event.created_at
                    pomodoro['duration'] = duration
                    pomodoro['progress'] = max(0, min(100, ceil(duration / self.pomodoro_duration * 100)))
                    pomodoro['overflow'] = duration > (self.pomodoro_duration + self.pomodoro_grace)
                    start_time = None
                    if pomodoro['end'] is not None and pomodoro['end'] > today_start:
                        pomodoro['today'] = True
            if pomodoro:
                pomodoros.append(pomodoro)
        except Exception as e:
            logger.warning(f'Could not calculate pomodoros for issue({issue.number}): {e}')
            logger.warning(f'Could not calculate pomodoros for issue({issue.number}): {event.label}')

        logger.warning(f'Pomodoros for issue({issue.number}): {pomodoros}')
        return pomodoros

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

    def _render_pomodoro(self, pomodoro: dict) -> str:
        progress = pomodoro['progress'] if pomodoro['progress'] else '0'
        out = f'''
<div class="worked{' active' if not pomodoro['end'] else ''}{' today' if pomodoro['today'] else ''}" data-start="{int(pomodoro['start'].timestamp())}" data-unit="{self.pomodoro_duration}" data-grace="{self.pomodoro_grace}">
<span class="start" title="{pomodoro['start'].date().isoformat()}">{pomodoro['start'].time().strftime('%H:%M')}</span>
<div class="progress-bar{' overflow' if pomodoro['overflow'] else ''}" data-duration="{self.pomodoro_duration}" 
     data-progress="{progress}" style="--progress: {progress}%;">
    <div class="progress"><p class="progress-label">{pomodoro['duration'] if pomodoro['duration'] else ''}</p></div>
</div>
<span class="end" title="{pomodoro['end'].date().isoformat() if pomodoro['end'] else ''}">{pomodoro['end'].time().strftime('%H:%M') if pomodoro['end'] else ''}</span>
</div>
        '''
        return out

    def _render_task(self, task) -> str:
        classes = ['task']
        for label in ('Stacked', 'Active', 'WIP', 'Important', 'Urgent'):
            if label in task['labels']:
                classes.append(label.lower())
        total_time = 0
        total_time_today = 0
        body = task['body'] or ''
        worked = ''
        logger.info(f'task: {task}')
        for pomodoro in task['pomodoros']:
            worked += self._render_pomodoro(pomodoro)
            total_time += pomodoro['duration'] if pomodoro['duration'] else 0
            total_time_today += pomodoro['duration'] if pomodoro['duration'] and pomodoro['today'] else 0
        logger.info(f'worked: {worked}')
        if total_time == 0:
            classes.append('untouched')
        out = f'''
<div class="{' '.join(classes)}">
    <a href="{task['url']}">{task['number']} {task['title']}</a>
    <details><summary>Description:</summary>
    {body}
    </details>
    <details{' open' if 'wip' in classes else ''}><summary>
    <div class="pomodoro-count">
        🍅: {len(task['pomodoros'])}
    </div>
    <div class="time-count">
        ⌛: {total_time} min ({ceil(total_time / self.pomodoro_duration)}) today: {total_time_today} min ({ceil(total_time_today / self.pomodoro_duration)})
    </div></summary>{worked}</details>
</div>
        '''
        return out

    def _generate_tasks_html(self, tasks) -> str:
        """Generate HTML for tasks without using a template file."""
        html = ['<div class="taskstack">']
        
        # Stacked tasks
        html.append('<div class="stacked-tasks">')
        html.append('<h2>Task Pipeline</h2>')
        for task in tasks['stacked']:
            html.append(self._render_task(task))
        html.append('</div>')
        
        # Active task
        if tasks['active']:
            html.append('<div class="active-task">')
            html.append('<h2>Current Task</h2>')
            task = tasks['active']
            progress = task.get('current_pomodoro', 0)
            html.append(self._render_task(task))
            html.append('</div>')
        
        # Today's tasks
        if tasks['today']:
            html.append('<div class="today-tasks">')
            html.append('<h2>Worked on Today</h2>')
            for task in tasks['today']:
                html.append(self._render_task(task))
            html.append('</div>')
        
        # Done tasks
        if tasks['done']:
            html.append('<div class="done-tasks">')
            html.append('<h2>Completed Today</h2>')
            for task in tasks['done']:
                html.append(self._render_task(task))
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
