from setuptools import setup, find_packages

setup(
    name='eakins_camera_control',
    version='1',
    packages=find_packages(),
    package_data={'': ['commands.json']},
    install_requires=[
        'argparse',
    ],
    entry_points={
        'console_scripts': [
            'eakins = eakins_camera_control.eakins_control:main',
        ],
    },
)

