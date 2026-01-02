# Cindergrace Git GUI (Tkinter)

## Project Overview

This project is a lightweight, cross-platform Git GUI application built with Python and the Tkinter library. It provides a user-friendly interface for common Git operations, aiming to simplify daily development workflows. Key features include repository management, staging, committing, branch management, and integration with the OpenRouter API for AI-powered commit message suggestions.

**Main Technologies:**
*   **Backend:** Python 3.10+
*   **UI:** Tkinter
*   **Dependencies:** `requests` for API calls, `cryptography` for secure API key storage.
*   **Testing:** `pytest`

**Architecture:**
The application follows a modular structure:
*   `main.py`: The main entry point, containing all the Tkinter UI code and event handling.
*   `git_ops.py`: A helper module that abstracts Git command-line operations.
*   `storage.py`: Handles the persistence of user data, such as favorite repositories and profiles, in JSON format.
*   `openrouter.py`: Manages the interaction with the OpenRouter API, including the encryption and decryption of the user's API key.
*   `prompt_builder.py`: A simple module for formatting the prompt sent to the OpenRouter API.

## Building and Running

### Setup

The project uses a Python virtual environment to manage dependencies. The `start.sh` script automates the setup process.

1.  **Create the virtual environment and install dependencies:**
    ```bash
    ./start.sh
    ```
    This command will create a `.venv` directory, install the required packages from `pyproject.toml`, and create a marker file to indicate that the installation is complete.

2.  **Run the application:**
    ```bash
    ./start.sh
    ```
    If the virtual environment and dependencies are already set up, the script will directly launch the application.

### Running Tests

The project uses `pytest` for testing. To run the tests, execute the following command:

```bash
python3 -m pytest -q
```

## Development Conventions

*   **Code Style:** The code appears to follow standard Python conventions (PEP 8), although no specific linter configuration is provided.
*   **Modularity:** The codebase is organized into modules with specific responsibilities, promoting separation of concerns.
*   **Error Handling:** The application uses `try...except` blocks to handle potential errors, such as missing files or invalid user input, and provides feedback to the user through message boxes.
*   **Concurrency:** The application uses the `threading` module to run Git operations asynchronously, preventing the UI from freezing during long-running commands. A `queue` is used to communicate between the worker threads and the main UI thread.
*   **Security:** The OpenRouter API key is encrypted using the `cryptography` library and stored in a local configuration file. The key is decrypted in memory with a user-provided password for each session.

## Key Files

*   `main.py`: The core of the application, responsible for the UI and event handling.
*   `git_ops.py`: Contains functions for executing Git commands.
*   `storage.py`: Manages loading and saving user data (favorites, profiles).
*   `openrouter.py`: Handles communication with the OpenRouter API for AI commit messages.
*   `prompt_builder.py`: Creates the prompt for the AI model.
*   `pyproject.toml`: Defines project metadata and dependencies.
*   `start.sh`: The main script for setting up the environment and running the application.
*   `README.md`: Provides a general overview of the project.
*   `tests/`: Contains unit tests for the project.
