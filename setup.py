from setuptools import setup, find_packages

setup(
    name="intoppy_time_ok",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-login',
        'flask-migrate',
        'flask-mail',
        'flask-moment',
    ],
) 