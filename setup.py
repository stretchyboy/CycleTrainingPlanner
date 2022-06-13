# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read().splitlines()

with open('test-requirements.txt') as requirements_file:
    test_requirements = requirements_file.read().splitlines()

setup(
    name='CycleTrainingPlanner',
    version='0.1.0',
    description='Making Cycling Training Plans Fast.',
    author='Martyn Eggleton',
    author_email='martyn.eggleton@gmail.com',
    url='https://github.com/stretchyboy/CycleTrainingPlanner',
    license='MIT',
    entry_points={
        'console_scripts': [
            'CycleTrainingPlanner=CycleTrainingPlanner:main',
        ],
    },
    py_modules = ['CycleTrainingPlanner'],
    packages=find_packages(exclude=('tests', 'docs')),
    python_requires='>=3.7',
    install_requires=requirements,
    tests_require=requirements + test_requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Documentation",
    ],
    keywords=["cycling"],
)
