# Accessing the data and using the notebook

Welcome! This guide will walk you through setting up your environment, ingesting data, and more.

---

## 1. Clone the competition repository

```bash
git clone https://github.com/dssg-nyc/stop-super-speeders-hackathon 
cd stop-super-speeders-hackathon
```

## 2. Install uv for python code(alternative to pip for package management)

**uv** is an extremely fast Python package manager that simplifies creating and managing Python projects. We’ll install it first to ensure our Python environment is ready to go. uv makes working with python both faster and simpler.

### Install uv

In VSCode, at the top of the screen, you will see an option that says **Terminal**. Then, you should click the button, and then select **New Terminal**. Then, copy and paste the following commands to install uv. You can double check they are the correct scripts by going to the official uv site, maintained by the company astral.

[Install uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)

```macOS, WSL, and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If you are using Windows and also not using WSL.

Windows Powershell:
```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Test your install by running in the terminal:
```sh
uv
```

#### Expected output:
If uv was installed correctly, you should see a help message that starts with:

```sh
An extremely fast Python package manager.

Usage: uv [OPTIONS] <COMMAND>

Commands:
  run      Run a command or script
  init     Create a new project
  ...
  help     Display documentation for a command
```

#### If you get an error:
- Copy and paste the exact error message into Google Ai Studio and explain you’re having problems using uv.
- Gemini can help troubleshoot your specific error message.

If uv displays its usage information without an error, congratulations! You’re all set to work with Python in your local environment.

## 3. Set up your environment

### 1. Set up your venv:
```sh
uv venv
```

### 2a. Activate your venv(Linux/MAC):
```sh
source .venv/bin/activate
```
### 2b. Activate your venv(Windows):
```sh
.venv\Scripts\activate
```

### 3. Install Libraries:
```sh
uv sync
```


## 4. Conduct your analysis

### Using a notebook

- Open the provided notebook(s) under `notebooks/` (e.g. `Hackathon.ipynb`).  
- In the top right corner, click Select Kernel, and choose this venv
- Use **DuckDB** to query downloaded and local data with SQL  
- The data urls are public, so feel free to use **Polars**, **Pandas**, or your preferred engine to query instead of DuckDB
- Develop your analysis and save outputs under `exports/`
- Save SQL queries for a SQL analytics pipeline in the .sql folder
