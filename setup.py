from setuptools import setup

setup(name='telegram-utils',
      version='0.1',
      description=
      'An Interface to a Telegram Bot to send and receive messages from.',
      url='https://github.com/TiborVoelcker/Telegram-Utils',
      author='Tibor Völcker',
      author_email='tiborvoelcker@hotmail.de',
      license='MIT',
      packages=['telegram_utils'],
      install_requires=[
            'python-telegram-bot',
      ],
      zip_safe=False)
