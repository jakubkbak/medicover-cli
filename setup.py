from setuptools import setup, find_packages


setup(
    name='medicover-cli',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests', 'bs4', 'click'
    ],
    entry_points={
        'console_scripts': ['medicover=medicover.main:main']
    }
)