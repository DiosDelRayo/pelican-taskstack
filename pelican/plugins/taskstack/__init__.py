from pelican import signals
from .taskstack import TaskStack

# Global instance to ensure availability
_taskstack_instance = None

def get_taskstack_instance():
    global _taskstack_instance
    return _taskstack_instance

def register():
    """Register the plugin with Pelican."""
    def initialized(pelican):
        global _taskstack_instance
        _taskstack_instance = TaskStack(pelican)
        # Store instance in settings for access by content generator
        pelican.settings['taskstack_instance'] = _taskstack_instance
        return _taskstack_instance

    def inject_taskstack_content(content):
        if hasattr(content, '_content'):
            taskstack = get_taskstack_instance()
            if taskstack:
                taskstack.inject_content(content)

    def add_taskstack_to_context(generator, metadata):
        metadata['taskstack_instance'] = get_taskstack_instance()

    signals.initialized.connect(initialized)
    signals.content_object_init.connect(inject_taskstack_content)
    signals.page_generator_context.connect(add_taskstack_to_context)
    signals.article_generator_context.connect(add_taskstack_to_context)
