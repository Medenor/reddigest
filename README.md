![Reddigest logo](https://repository-images.githubusercontent.com/1031369014/18acd53d-4fc0-43d0-9520-0b830c9040fb)

# Reddigest - Reddit Threads Digest

## Description
Reddigest is a Python application designed to generate digests from Reddit posts. It allows users to link a thread from a subreddit, and then generate a summary in Markdown format. The application also features a graphical user interface (GUI) for ease of use.

## Features
*   Generate digests from specified subreddits.
*   Two summarizing approches: Top 5 comments or AI summary (OpenAI or Gemini)
*   Bring Your Own Keys (BYOK) for AI features
*   Output digests in Markdown format.
*   User-friendly Graphical User Interface (GUI).
*   Save generated digests to clipboard.

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

4.  **Configure PRAW (Reddit API Wrapper):**
    This application uses PRAW to interact with the Reddit API. You need to set up your Reddit API credentials.
    *   Rename `praw-example.ini` to `praw.ini`.
    *   Edit `praw.ini` and fill in your Reddit API credentials (client ID, client secret, user agent, username, password). You can create a Reddit API application [here](https://www.reddit.com/prefs/apps).
    *   AI features are available on a bring-your-own-key (BYOK) basis, meaning you are responsible for any associated costs with enabling and using these features.

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
