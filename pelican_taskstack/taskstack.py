import os
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
        self._init_github()

    def _get_github_token(self):
        """Get GitHub token from environment or settings."""
        return os.environ.get('GITHUB_TOKEN') or self.settings.get('GITHUB_TOKEN')

    def _init_github(self):
        """Initialize GitHub connection."""
        if not self.github_token:
            raise ValueError("GitHub token not found in environment or settings")
        self.gh = login(token=self.github_token)
        repo_full_name = os.environ.get('GITHUB_REPOSITORY') or self.settings.get('GITHUB_REPOSITORY')
        owner, repo = repo_full_name.split('/')
        self.repo = self.gh.repository(owner, repo)

    def get_tasks(self):
        """Fetch and process GitHub issues."""
        tasks = {
            'stacked': [],
            'active': None,
            'wip': None,
            'today': []
        }

        for issue in self.repo.issues(labels=['Stacked', 'Active', 'WIP']):
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

    def generate_output(self, writer):
        """Generate HTML output for task stack."""
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

        # Copy static files
        self._copy_static_files(writer)

    def _copy_static_files(self, writer):
        """Copy CSS and JS files to output."""
        static_path = os.path.join(os.path.dirname(__file__), 'static')
        
        for root, _, files in os.walk(static_path):
            for file in files:
                src = os.path.join(root, file)
                rel_path = os.path.relpath(src, static_path)
                dst = os.path.join(self.settings['OUTPUT_PATH'], 'theme/taskstack', rel_path)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                writer.copy_file(src, dst)

def register():
    """Register the plugin with Pelican."""
    signals.initialized.connect(init_taskstack)

def init_taskstack(pelican):
    taskstack = TaskStack(pelican)
    signals.article_writer_finalized.connect(taskstack.generate_output)
