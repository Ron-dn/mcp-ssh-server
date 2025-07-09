#!/usr/bin/env python3
"""
Setup script for MCP SSH Server.

This setup.py provides backwards compatibility with older Python packaging systems
while the main configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure we're using Python 3.8+
if sys.version_info < (3, 8):
    print("ERROR: MCP SSH Server requires Python 3.8 or higher")
    sys.exit(1)

# Read README for long description
def read_readme():
    """Read README.md for long description."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "A powerful, generic SSH MCP server for secure remote system access"

# Read requirements
def read_requirements():
    """Read requirements.txt for dependencies."""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "paramiko>=3.0.0",
            "mcp>=0.1.0",
            "pydantic>=2.0.0",
            "typing-extensions>=4.0.0",
            "cryptography>=41.0.0",
        ]

# Get version from package
def get_version():
    """Get version from package."""
    try:
        from mcp_ssh_server import __version__
        return __version__
    except ImportError:
        return "1.0.0"

setup(
    name="mcp-ssh-server",
    version=get_version(),
    description="A powerful, generic SSH MCP server for secure remote system access",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="MCP SSH Server Contributors",
    author_email="contributors@mcp-ssh-server.com",
    url="https://github.com/yourusername/mcp-ssh-server",
    project_urls={
        "Homepage": "https://github.com/yourusername/mcp-ssh-server",
        "Repository": "https://github.com/yourusername/mcp-ssh-server",
        "Documentation": "https://github.com/yourusername/mcp-ssh-server/wiki",
        "Bug Tracker": "https://github.com/yourusername/mcp-ssh-server/issues",
        "Changelog": "https://github.com/yourusername/mcp-ssh-server/blob/main/CHANGELOG.md",
    },
    
    # Package discovery
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Dependencies
    install_requires=read_requirements(),
    python_requires=">=3.8",
    
    # Entry points
    entry_points={
        "console_scripts": [
            "mcp-ssh-server=mcp_ssh_server.server:main",
        ],
    },
    
    # Package metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications",
        "Topic :: Security",
        "Topic :: Internet",
    ],
    
    keywords=[
        "mcp", "ssh", "remote", "automation", "server", "protocol",
        "network", "system", "administration", "devops", "infrastructure"
    ],
    
    # Additional files
    include_package_data=True,
    zip_safe=False,
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
        "testing": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "coverage>=7.0.0",
        ],
    },
    
    # License
    license="MIT",
    
    # Platforms
    platforms=["any"],
)

# Post-install message
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MCP SSH Server Installation Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Add to your MCP client configuration:")
    print('   {"mcpServers": {"ssh": {"command": "mcp-ssh-server"}}}')
    print("\n2. Start using SSH tools in your MCP client:")
    print("   - mcp_ssh_connect")
    print("   - mcp_ssh_execute")
    print("   - mcp_ssh_upload/download")
    print("   - And 10+ more tools!")
    print("\n3. Check examples in the examples/ directory")
    print("\n📖 Documentation: https://github.com/yourusername/mcp-ssh-server")
    print("🐛 Issues: https://github.com/yourusername/mcp-ssh-server/issues")
    print("="*60) 