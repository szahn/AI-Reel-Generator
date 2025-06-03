from setuptools import setup, find_packages

setup(
    name="reel-generator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytubefix",
        "azure-identity",
        "azure-storage-blob",
        "python-dotenv",
        "firebase-admin",
    ],
    python_requires=">=3.8",
    author="Reel Generator",
    description="A tool for generating video reels from longer videos",
    long_description=open("Readme.md").read(),
    long_description_content_type="text/markdown",    
) 