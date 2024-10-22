from .taskstack import TaskStack

def register():
    """Register the plugin with Pelican."""
    signals.initialized.connect(init_taskstack)
    signals.content_object_init.connect(inject_taskstack_content)

def init_taskstack(pelican):
    """Initialize the TaskStack plugin."""
    return TaskStack(pelican)

def inject_taskstack_content(content):
    """Inject taskstack content into articles and pages."""
    if not hasattr(content, '_content'):
        return
    
    taskstack = content.settings['taskstack_instance']
    taskstack.inject_content(content)

