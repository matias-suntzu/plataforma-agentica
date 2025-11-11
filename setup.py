from setuptools import setup, find_packages

setup(
    name="agente-meta-mcp-personal",
    version="0.1.0",
    packages=find_packages(include=['langgraph_agent*', 'tool_server_api*']),
    python_requires=">=3.8",
)