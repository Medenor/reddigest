![Reddigest logo](https://repository-images.githubusercontent.com/1031369014/18acd53d-4fc0-43d0-9520-0b830c9040fb)

# Reddigest - Reddit Threads Digest

## Description
Reddigest is a Python application designed to generate digests from Reddit posts. It allows users to link a thread from a subreddit, and then generate a summary in Markdown format. The application also features a graphical user interface (GUI) for ease of use.

## Features
*   Generate digests from specified subreddits.
*   Two summarizing approaches: Top 5 comments or AI summary (OpenAI or Gemini) with configurable detail levels (Concise, Standard, Detailed).
*   Bring Your Own Keys (BYOK) for AI features.
*   Output digests in Markdown format.
*   User-friendly Graphical User Interface (GUI).
*   Save generated digests to clipboard.
*   Digest History: View and manage previously generated digests, including the ability to delete entries and copy their content directly from the history window.

## Installation

To set up and run Reddigest, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Medenor/reddigest.git
    cd reddigest
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Credentials (Reddit & AI):**
    This application interacts with the Reddit API (via PRAW) and optionally with OpenAI or Google Gemini for AI summarization. You need to set up your API credentials.

    **Recommended Method: Environment Variables (for security and flexibility)**
    It is highly recommended to use environment variables to store your sensitive API keys. The application will prioritize these variables over `praw.ini`.

    Create a file named `.env` in the root directory of the project (the same directory as `main.py` and `reddit_digest.py`). Add your credentials to this file in the format `KEY=VALUE`. This file should be added to your `.gitignore` (it already is by default).

    Example `.env` file:
    ```
    REDDIT_CLIENT_ID="your_reddit_client_id"
    REDDIT_CLIENT_SECRET="your_reddit_client_secret"
    REDDIT_USER_AGENT="Reddit Digest App by u/YourRedditUsername"
    # Optional, if using password-based authentication:
    # REDDIT_USERNAME="your_reddit_username"
    # REDDIT_PASSWORD="your_reddit_password"

    OPENAI_API_KEY="your_openai_api_key"
    GOOGLE_GEMINI_API_KEY="your_google_gemini_api_key"
    ```
    You can create a Reddit API application [here](https://www.reddit.com/prefs/apps).

    **Alternative Method: `praw.ini` file**
    If you prefer not to use environment variables, you can still use the `praw.ini` file.
    *   Rename `praw-example.ini` to `praw.ini`.
    *   Edit `praw.ini` and fill in your Reddit API credentials (client ID, client secret, user agent, username, password) and AI API keys.
    *   Note: Values in environment variables will override values in `praw.ini`.

    AI features are available on a bring-your-own-key (BYOK) basis, meaning you are responsible for any associated costs with enabling and using these features.

## Usage

To run the application, ensure your virtual environment is activated and execute the main GUI script:

```bash
source .venv/bin/activate
python reddit_digest_gui.py
```

This will launch the graphical interface where you can configure your digest generation options.

### Summary Methods

This project offers two main approaches for generating summaries:

- **Top 5 Comments**  
  Displays the five most relevant or insightful comments to quickly gain community-based insight.

- **AI Summary (OpenAI or Gemini)**  
  Utilizes an advanced language model (OpenAI or Gemini) to produce an overall summary, synthesizing the key points of the content.
  By default, "gpt-4.1-nano" (OpenAI) and "gemini-2.5-flash" (Google Gemini) are set as default summarization models in `model_preferences.json`. These are low costs models from both providers, with high context windows suitable for Reddit threads.

**When to use each method:**  
- Prefer **Top 5 Comments** for a quick, community-driven overview.  
- Use the **AI Summary** for a comprehensive, automatically generated synthesis.

## Contribution

Contributions are welcome! If you wish to improve PromptVault, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/new-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add a new feature'`).
5.  Push to the branch (`git push origin feature/new-feature`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
Reddit and all related trademarks, logos, and other proprietary elements are owned by Reddit. This project is not affiliated with or endorsed by Reddit.
