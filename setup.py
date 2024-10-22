from setuptools import setup, find_packages

setup(
    name='pelican-taskstack',
    version='0.2.3',
    description='Pelican plugin for visualizing TaskStacks',
    author='DiosDelRayo',
    packages=find_packages(),
    include_package_data=True,  # This is important to include static files
    install_requires=[
        'github3.py>=3.0.0',
        'pelican>=4.0.0',
        'markdown>=3.0',
    ],
    entry_points={
        'pelican.plugins': [
            'pelican_taskstack = pelican.plugins.pelican_taskstack:register'
        ]
    },
)
