from setuptools import setup, find_packages

setup(
    name='pelican-taskstack',
    version='0.1.0',
    description='Pelican plugin for visualizing TaskStacks',
    author='DiosDelRayo',
    packages=find_packages(),
    install_requires=[
        'github3.py>=3.0.0',
        'pelican>=4.0.0',
        'markdown>=3.0',
    ],
    entry_points={
        'pelican.plugins': [
            'taskstack = pelican_taskstack.taskstack:register',
        ]
    },
    package_data={
        'pelican_taskstack': [
            'static/css/*.css',
            'static/js/*.js',
            'templates/*.html'
        ],
    },
)
