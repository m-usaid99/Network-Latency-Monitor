from setuptools import setup, find_packages

setup(
    name="network-latency-monitor",  # Replace with your package name
    version="0.1.0",
    author="Muhammad Usaid Rehman",
    author_email="rehman.usaid@gmail.com",
    description="A real-time network latency monitoring CLI tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your_project",  # Replace with your repository URL
    packages=find_packages(),
    install_requires=[
        "rich",
        "asciichartpy",
        "pandas",
        "seaborn",
        "matplotlib",
        "ipaddress",
    ],
    entry_points={
        "console_scripts": [
            "network-latency-monitor=network_latency_monitor.main:cli",  # Replace with your main function
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
