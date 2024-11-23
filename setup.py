from setuptools import setup, find_namespace_packages

setup(
    name='pelican-taskstack',
    version='0.4.1',
    description='Pelican plugin for visualizing TaskStacks',
    author='DiosDelRayo',
    packages=find_namespace_packages(include=['pelican.*']),
    include_package_data=True,
    data_files=[
        ('pelican/static/css', ['pelican/static/css/taskstack.css']),
        ('pelican/static/js', ['pelican/static/js/taskstack.js']),
        ('pelican/templates', ['pelican/templates/taskstack.html']),
    ],
    install_requires=[
        'github3.py>=3.0.0',
        'pelican>=4.0.0',
        'markdown>=3.0',
    ],
    entry_points={
        'pelican.plugins': [
            'taskstack = pelican.plugins.taskstack:register'
        ]
    },
)
