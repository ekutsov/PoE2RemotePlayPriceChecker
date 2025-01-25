from setuptools import setup

APP = ['main.py']  # Ваш основной скрипт
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'MyApp',
        'CFBundleIdentifier': 'com.mycompany.myapp',
        # 'LSUIElement': True, # если нужно скрывать из Dock
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)