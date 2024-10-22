from setuptools import setup, find_namespace_packages

setup(
    name='pelican-taskstack',
    version='0.2.8',
    description='Pelican plugin for visualizing TaskStacks',
    author='DiosDelRayo',
    packages=find_namespace_packages(include=['pelican.*']),
    include_package_data=True,
    package_data={
        'pelican.plugins.taskstack': [
            'static/css/*.css',
            'static/js/*.js',
            'templates/*.html',
        ],
    },
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
