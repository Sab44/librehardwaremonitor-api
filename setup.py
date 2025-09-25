from setuptools import setup

setup(
    name='librehardwaremonitor-api',
    version='1.4.0',
    package_data={'librehardwaremonitor_api': ['py.typed']},
    packages=['librehardwaremonitor_api'],
    install_requires=[
        'aiohttp'
    ],
    author='Sab44',
    author_email='64696149+Sab44@users.noreply.github.com',
    description='A Python API client for LibreHardwareMonitor',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Sab44/librehardwaremonitor-api',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)
