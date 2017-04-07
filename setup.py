from setuptools import setup

setup(
    name='dimoha-pylibs',
    version='0.0.1',
    description='Pylibs for development',
    author=', '.join((
        'Dimoha <dimoha@controlstyle.ru',
    )),
    author_email='dimoha@controlstyle.ru',
    url='http://gitlab.controlstyle.ru/Dimoha/pylibs/',
    install_requires=[
        'requests[security]==2.12.1',
    ]
)