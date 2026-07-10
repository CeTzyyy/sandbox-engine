from setuptools import setup, find_packages

setup(
    name="sandbox-engine",
    version="0.1.0",
    author="CeTzyyy",
    description="Эволюционный движок экосистемы на Python",
    license="Proprietary / SandBox Engine License", 
    packages=find_packages(),
    install_requires=[
        "Pillow",
    ],
    python_requires=">=3.11",
)
