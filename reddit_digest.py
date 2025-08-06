import praw
import re
import configparser
import os
from urllib.parse import urlparse
import html
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Try to import OpenAI and Google Generative AI libraries
try:
    import openai
except ImportError:
    openai = None
    print("Warning: OpenAI library not found. Install with 'pip install openai' to use OpenAI summarization.")

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    print("Warning: Google Generative AI library not found. Install with 'pip install google-generativeai' to use Gemini summarization.")

def get_available_openai_models():
    if not openai:
        return []
    api_keys = load_api_keys()
    api_key = api_keys.get('openai_api_key')
    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        return ["gpt-3.5-turbo", "gpt-4", "gpt-4o"] # Fallback to common models

    openai.api_key = api_key
    try:
        models = openai.models.list()
        # Filter for chat completion models
        chat_models = [m.id for m in models.data if "gpt" in m.id and "instruct" not in m.id and "embedding" not in m.id]
        chat_models.sort()
        return chat_models
    except Exception as e:
        print(f"Error fetching OpenAI models: {e}")
        return ["gpt-3.5-turbo", "gpt-4", "gpt-4o"] # Fallback

def get_available_gemini_models():
    if not genai:
        return []
    api_keys = load_api_keys()
    api_key = api_keys.get('google_gemini_api_key')
    if not api_key or api_key == "YOUR_GOOGLE_GEMINI_API_KEY":
        return ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"] # Fallback to common models

    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        # Filter for models that support text generation
        generative_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        generative_models.sort()
        return generative_models
    except Exception as e:
        print(f"Error fetching Gemini models: {e}")
        return ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"] # Fallback

def load_api_keys():
    api_keys = {}

    # Try to load API keys from environment variables first
    api_keys['openai_api_key'] = os.getenv('OPENAI_API_KEY')
    api_keys['google_gemini_api_key'] = os.getenv('GOOGLE_GEMINI_API_KEY')

    # Load Reddit credentials from environment variables
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    reddit_user_agent = os.getenv('REDDIT_USER_AGENT')
    reddit_username = os.getenv('REDDIT_USERNAME')
    reddit_password = os.getenv('REDDIT_PASSWORD')

    # If not found in environment variables, try to load from praw.ini
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'praw.ini')
    config.read(config_path)

    if 'api_keys' in config:
        if not api_keys['openai_api_key']:
            api_keys['openai_api_key'] = config.get('api_keys', 'openai_api_key', fallback=None)
        if not api_keys['google_gemini_api_key']:
            api_keys['google_gemini_api_key'] = config.get('api_keys', 'google_gemini_api_key', fallback=None)
    
    # Load Reddit credentials from praw.ini if not found in environment variables
    reddit_creds = {}
    if 'default' in config:
        if not reddit_client_id:
            reddit_creds['client_id'] = config.get('default', 'client_id', fallback=None)
        if not reddit_client_secret:
            reddit_creds['client_secret'] = config.get('default', 'client_secret', fallback=None)
        if not reddit_user_agent:
            reddit_creds['user_agent'] = config.get('default', 'user_agent', fallback=None)
        if not reddit_username:
            reddit_creds['username'] = config.get('default', 'username', fallback=None)
        if not reddit_password:
            reddit_creds['password'] = config.get('default', 'password', fallback=None)

    # Combine environment variables and praw.ini for Reddit credentials
    api_keys['reddit_creds'] = {
        'client_id': reddit_client_id or reddit_creds.get('client_id'),
        'client_secret': reddit_client_secret or reddit_creds.get('client_secret'),
        'user_agent': reddit_user_agent or reddit_creds.get('user_agent'),
        'username': reddit_username or reddit_creds.get('username'),
        'password': reddit_password or reddit_creds.get('password')
    }

    return api_keys

def validate_reddit_url(url):
    # Enhanced URL validation for Reddit URLs
    # Check if URL is None or empty
    if not url:
        return False, "URL is required"
    
    # Parse the URL
    try:
        parsed_url = urlparse(url)
    except Exception:
        return False, "Invalid URL format"
    
    # Check scheme
    if parsed_url.scheme not in ['http', 'https']:
        return False, "URL must use HTTP or HTTPS"
    
    # Check domain (whitelisting)
    allowed_domains = ['reddit.com', 'www.reddit.com']
    if parsed_url.netloc not in allowed_domains:
        return False, f"Domain not allowed. Allowed domains: {', '.join(allowed_domains)}"
    
    # Check path structure using more comprehensive regex
    path_pattern = r'^/r/([^/]+)/comments/([^/]+)(/[^/]*)?/?$'
    match = re.match(path_pattern, parsed_url.path)
    
    if not match:
        return False, "Invalid Reddit URL structure. Expected format: https://www.reddit.com/r/subreddit/comments/post_id/"
    
    subreddit = match.group(1)
    post_id = match.group(2)
    
    # Additional validation for subreddit and post_id
    if not subreddit or not post_id:
        return False, "Invalid subreddit or post ID"
    
    # Check for potentially malicious characters
    if re.search(r'[<>"\']', subreddit) or re.search(r'[<>"\']', post_id):
        return False, "Invalid characters in subreddit or post ID"
    
    return True, "Valid URL"

def sanitize_input(text):
    # Sanitize user input to prevent XSS
    if not text:
        return ""
    # Remove or escape potentially dangerous characters
    sanitized = html.escape(text)
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    return sanitized

def summarize_with_openai(comments, api_key, model_name, detail_level="standard"):
    if not openai:
        return "OpenAI library not installed."
    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        return "OpenAI API key not configured in praw.ini."

    openai.api_key = api_key
    
    comment_text = "\n".join(comments)
    
    if detail_level == "concise":
        prompt_instruction = "Summarize the whole Reddit thread very concisely, in 1-2 sentences:"
        max_tokens_val = 100
    elif detail_level == "detailed":
        prompt_instruction = "Summarize the whole Reddit thread in great detail, including all key arguments, counter-arguments, and important nuances. Aim for a comprehensive summary of the Reddit thread as a whole:"
        max_tokens_val = 1000
    else: # standard
        prompt_instruction = "Summarize the whole Reddit thread:"
        max_tokens_val = 500

    prompt = f"{prompt_instruction}\n\n{comment_text}\n\nSummary:"

    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes Reddit comments."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens_val
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error summarizing with OpenAI: {e}"

def summarize_with_gemini(comments, api_key, model_name, detail_level="standard"):
    if not genai:
        return "Google Generative AI library not installed."
    if not api_key or api_key == "YOUR_GOOGLE_GEMINI_API_KEY":
        return "Google Gemini API key not configured in praw.ini."

    genai.configure(api_key=api_key)
    
    comment_text = "\n".join(comments)
    
    if detail_level == "concise":
        prompt_instruction = "Summarize the following Reddit comments very concisely, in 1-2 sentences:"
    elif detail_level == "detailed":
        prompt_instruction = "Summarize the following Reddit comments in great detail, including all key arguments, counter-arguments, and important nuances. Aim for a comprehensive summary of the whole Reddit thread:"
    else: # standard
        prompt_instruction = "Summarize the following Reddit comments:"

    prompt = f"{prompt_instruction}\n\n{comment_text}\n\nSummary:"

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error summarizing with Google Gemini: {e}"

def get_reddit_digest(url, summarization_method="top5", model_name=None, detail_level=None):
    # Enhanced URL validation
    is_valid, message = validate_reddit_url(url)
    if not is_valid:
        return f"Invalid Reddit URL: {message}"
    
    # Parse URL to extract components
    parsed_url = urlparse(url)
    path_pattern = r'^/r/([^/]+)/comments/([^/]+)(/[^/]*)?/?$'
    match = re.match(path_pattern, parsed_url.path)
    
    subreddit_name = match.group(1)
    submission_id = match.group(2)

    api_keys = load_api_keys()

    try:
        # Initialize PRAW with your Reddit API credentials
        # Initialize PRAW with your Reddit API credentials
        # These can be configured in environment variables or a praw.ini file
        # Environment variables take precedence.
        # For more info: https://praw.readthedocs.io/en/stable/getting_started/quickstart.html#oauth-quick-start
        reddit_creds = api_keys.get('reddit_creds', {})
        
        reddit = praw.Reddit(
            client_id=reddit_creds.get('client_id'),
            client_secret=reddit_creds.get('client_secret'),
            user_agent=reddit_creds.get('user_agent'),
            username=reddit_creds.get('username'),
            password=reddit_creds.get('password')
        )
        reddit.read_only = True # We are only reading data

        submission = reddit.submission(id=submission_id)
        submission.comments.replace_more(limit=0) # Flatten comments, remove "More Comments"

        title = sanitize_input(submission.title)
        digest = f"# Reddit Digest: {title}\n\n"

        if submission.selftext:
            digest += f"## Post Content:\n{sanitize_input(submission.selftext)}\n\n"
        elif submission.url and not submission.is_self:
            digest += f"## Post Link:\n{sanitize_input(submission.url)}\n\n"

        all_comments = []
        for top_level_comment in submission.comments:
            if isinstance(top_level_comment, praw.models.Comment):
                all_comments.append(sanitize_input(top_level_comment.body))
        
        if not all_comments:
            digest += "No top-level comments found.\n\n"
            return digest

        if summarization_method == "top5":
            digest += "## Top 5 Comments:\n\n"
            comment_count = 0
            for comment_body in all_comments:
                if comment_count >= 5:
                    break
                digest += f"- **Comment {comment_count+1}:** {comment_body}\n"
                comment_count += 1
            digest += "\n"
        elif summarization_method == "openai":
            digest += f"## OpenAI Summary of Comments (Model: {model_name or 'default'}):\n\n"
            summary = summarize_with_openai(all_comments, api_keys.get('openai_api_key'), model_name)
            digest += f"{summary}\n\n"
        elif summarization_method == "gemini":
            digest += f"## Google Gemini Summary of Comments (Model: {model_name or 'default'}):\n\n"
            summary = summarize_with_gemini(all_comments, api_keys.get('google_gemini_api_key'), model_name)
            digest += f"{summary}\n\n"
        else:
            digest += "## Top 5 Comments (Default):\n\n"
            comment_count = 0
            for comment_body in all_comments:
                if comment_count >= 5:
                    break
                digest += f"- **Comment {comment_count+1}:** {comment_body}\n"
                comment_count += 1
            digest += "\n"

    except Exception as e:
        return f"Error fetching Reddit content or summarizing: {e}\n\nPlease ensure your praw.ini file is correctly configured with your Reddit API credentials and API keys for summarization services if used."

    return digest
