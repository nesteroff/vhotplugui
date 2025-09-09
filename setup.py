from setuptools import setup, find_packages

setup(
    name="vhotplugui",
    version="1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "vhotplugui=vhotplugui.vhotplugui:main",
        ],
    },
)
