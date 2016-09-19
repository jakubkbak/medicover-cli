from setuptools import setup


setup(
    name='Medicover-CLI',
    version='1.0',
    py_modules=['cli'],
    install_requires=[
        'requests', 'bs4', 'click'
    ],
    entry_points={
        'console_scripts': ['medicover=cli:main']
    }
)