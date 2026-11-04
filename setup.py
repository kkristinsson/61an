from setuptools import find_packages, setup


setup(
    name="kapell",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests==2.33.0",
        "click==8.1.7",
        "python-dotenv==1.2.2",
        "Flask==3.1.3",
    ],
    entry_points={
        "console_scripts": [
            "kapell=kapell.cli:cli",
            "kapell-cli=kapell.cli:cli",
            "kapell-web=kapell.web:main",
        ]
    },
)

