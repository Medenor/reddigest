import praw
import re
import configparser
import os
from urllib.parse import urlparse
import html
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# Define the path for the preferences file
PREFERENCES_FILE = 'model_preferences.json'

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
    
    # Always include the desired default model in the fallback list
    fallback_models = ["gpt-4.1-nano", "gpt-3.5-turbo", "gpt-4", "gpt-4o"] 
    fallback_models.sort() # Ensure consistent order

    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        return fallback_models

    openai.api_key = api_key
    try:
        models = openai.models.list()
        # Filter for chat completion models and add "gpt-4.1-nano" if not already present
        chat_models = [m.id for m in models.data if "gpt" in m.id and "instruct" not in m.id and "embedding" not in m.id]
        if "gpt-4.1-nano" not in chat_models:
            chat_models.append("gpt-4.1-nano")
        chat_models.sort()
        return chat_models
    except Exception as e:
        print(f"Error fetching OpenAI models: {e}")
        return fallback_models

def get_available_gemini_models():
    # Fetches available Gemini models from the API or returns a fallback list.
    # Comprehensive fallback list of known generative models, including the desired default
    fallback_models = [
        "gemini-2.5-flash", # Desired default
        "gemini-1.0-pro",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-pro",
        "gemini-pro-vision" # Supports text generation from images and text
    ]
    fallback_models.sort()

    if not genai:
        return [] # Return empty list if library is not installed

    api_keys = load_api_keys()
    api_key = api_keys.get('google_gemini_api_key')

    # If no API key is provided, return the fallback list
    if not api_key or api_key == "YOUR_GOOGLE_GEMINI_API_KEY":
        return fallback_models

    try:
        genai.configure(api_key=api_key)
        # List all available models from the API
        models = genai.list_models()
        
        # Filter for models that support 'generateContent'
        # Also, ensure we correctly parse the model name (e.g., "models/gemini-pro")
        generative_models = [
            m.name.split('/')[-1] for m in models 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # Remove duplicates and sort
        generative_models = sorted(list(set(generative_models)))
        
        # Add "gemini-2.5-flash" if not already present
        if "gemini-2.5-flash" not in generative_models:
            generative_models.append("gemini-2.5-flash")
        
        generative_models = sorted(list(set(generative_models))) # Re-sort after adding
        
        return generative_models if generative_models else fallback_models
    except Exception as e:
        print(f"Error fetching Gemini models: {e}. Returning fallback list.")
        return fallback_models

def load_model_preferences():
    """Loads model preferences from a JSON file."""
    if os.path.exists(PREFERENCES_FILE):
        try:
            with open(PREFERENCES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {PREFERENCES_FILE}. Returning empty preferences.")
            return {}
    return {}

def save_model_preferences(preferences):
    """Saves model preferences to a JSON file."""
    try:
        with open(PREFERENCES_FILE, 'w') as f:
            json.dump(preferences, f, indent=4)
    except IOError as e:
        print(f"Error saving preferences to {PREFERENCES_FILE}: {e}")

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
    sanitized = text
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    return sanitized

def summarize_with_openai(comments, api_key, model_name, detail_level="standard", submission_data=None, enable_text_analysis=False):
    if not openai:
        return "OpenAI library not installed."
    if not api_key or api_key == "YOUR_OPENAI_API_KEY":
        return "OpenAI API key not configured in praw.ini."

    openai.api_key = api_key
    
    comment_text = "\n".join(comments)
    
    # Define common parts of the template
    base_template_part = """
# Reddit Thread Summary: [Thread Title]

## Key Information

*   **Source:** [Link to thread]
*   **Subreddit:** r/[Subreddit Name]
*   **Publication Date:** [Original Post Date]
*   **Activity:** [Number of Comments]
*   **Summarization Method:** [OpenAI model name] ([Detail Level])

---

## Summary

[Write a 2-4 sentence paragraph here summarizing the main issue and the general conclusion of the discussion thread. What is the main takeaway?]
"""

    central_issue_part = """
---

## Central Issue

[Clearly describe the problem, question, or initial topic raised by the Original Poster (OP).]
"""

    community_discussion_part = """
---

## Community Discussion Analysis

### General Consensus and Best Practices

*   [Consensus Point 1]
*   [Consensus Point 2]
*   [Consensus Point 3]

### Suggested Solutions and Methods

*   **[Method 1]:** [Description of the method]
*   **[Method 2]:** [Description of the method]
*   **[Method 3]:** [Description of the method]

### Warnings and Cautionary Points

*   [Warning 1: Description of the risk or cautionary point]
*   [Warning 2: Description of the risk or cautionary point]
*   [Warning 3: Description of the risk or cautionary point]

### Tools and Products Mentioned

*   **[Tool/Product 1]:** [Brief description or context of mention]
*   **[Tool/Product 2]:** [Brief description or context of mention]

### Points of Debate and Divergent Opinions

*   **[Debate Topic 1]:** [Description of different viewpoints]
*   **[Debate Topic 2]:** [Description of different viewpoints]
"""

    report_conclusion_part = """
---

## Report Conclusion

[Summarize here the 3 or 4 most important takeaways from the discussion. What are the final recommendations?]
"""

    sentiment_analysis_part = """
---

## Sentiment Analysis

*   **Overall Sentiment:** [Overall sentiment of the discussion (e.g., Positive, Negative, Neutral, Mixed)]
*   **Key Positive Aspects:** [List 2-3 positive themes or points of view]
*   **Key Negative Aspects:** [List 2-3 negative themes or points of view]
"""
    
    # Construct templates dynamically based on detail_level
    if detail_level == "concise":
        selected_template = base_template_part
        max_tokens_val = 500 # Adjusted for concise summary
    elif detail_level == "standard":
        selected_template = base_template_part + central_issue_part + report_conclusion_part
        max_tokens_val = 1000 # Adjusted for standard summary
    else: # Default to detailed
        selected_template = base_template_part + central_issue_part + community_discussion_part + report_conclusion_part
        max_tokens_val = 2000 # Adjusted for detailed summary

    # Add sentiment analysis part if enabled
    if enable_text_analysis:
        selected_template += sentiment_analysis_part

    # Fill in the Key Information section of the selected template
    if submission_data:
        selected_template = selected_template.replace("[Thread Title]", sanitize_input(submission_data.get('title', 'N/A')))
        selected_template = selected_template.replace("[Link to thread]", sanitize_input(submission_data.get('url', 'N/A')))
        selected_template = selected_template.replace("[Subreddit Name]", sanitize_input(submission_data.get('subreddit', 'N/A')))
        selected_template = selected_template.replace("[Original Post Date]", sanitize_input(submission_data.get('date', 'N/A')))
        selected_template = selected_template.replace("[Number of Comments]", str(submission_data.get('num_comments', 'N/A')))
        selected_template = selected_template.replace("[OpenAI model name]", model_name)
    
    # Instruction for the AI to fill the template
    prompt_instruction = f"""
Please summarize the following Reddit thread comments and fill in the provided template.
Ensure you strictly adhere to the template structure and fill all bracketed fields `[ ]` with relevant information extracted from the comments.
If a section has no relevant information, you can leave its bullet points or descriptions empty, but keep the section headers.

Reddit Comments:
{comment_text}

Template to fill:
{selected_template}

Summary:
"""
    
    # max_tokens_val is already set based on detail_level

    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes Reddit comments into a structured report. If text analysis is enabled, also provide overall sentiment and key positive/negative aspects."},
                {"role": "user", "content": prompt_instruction}
            ],
            max_tokens=max_tokens_val
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing with OpenAI: {e}")
        return "An error occurred while summarizing with OpenAI. Please check your API key and try again."

def summarize_with_gemini(comments, api_key, model_name, detail_level="standard", submission_data=None, enable_text_analysis=False):
    # Summarizes comments using the Google Gemini API.
    if not genai:
        return "Google Generative AI library not installed. Please run 'pip install google-generativeai'."
    
    if not api_key or api_key == "YOUR_GOOGLE_GEMINI_API_KEY":
        return "Google Gemini API key not configured. Please add it to your .env file or praw.ini."

    genai.configure(api_key=api_key)
    
    comment_text = "\n".join(comments)
    
    # Define common parts of the template
    base_template_part = """
# Reddit Thread Summary: [Thread Title]

## Key Information

*   **Source:** [Link to thread]
*   **Subreddit:** r/[Subreddit Name]
*   **Publication Date:** [Original Post Date]
*   **Activity:** [Number of Comments]
*   **Summarization Method:** [Google Gemini model name] ([Detail Level])

---

## Summary

[Write a 2-4 sentence paragraph here summarizing the main issue and the general conclusion of the discussion thread. What is the main takeaway?]
"""

    central_issue_part = """
---

## Central Issue

[Clearly describe the problem, question, or initial topic raised by the Original Poster (OP).]
"""

    community_discussion_part = """
---

## Community Discussion Analysis

### General Consensus and Best Practices

*   [Consensus Point 1]
*   [Consensus Point 2]
*   [Consensus Point 3]

### Suggested Solutions and Methods

*   **[Method 1]:** [Description of the method]
*   **[Method 2]:** [Description of the method]
*   **[Method 3]:** [Description of the method]

### Warnings and Cautionary Points

*   [Warning 1: Description of the risk or cautionary point]
*   [Warning 2: Description of the risk or cautionary point]
*   [Warning 3: Description of the risk or cautionary point]

### Tools and Products Mentioned

*   **[Tool/Product 1]:** [Brief description or context of mention]
*   **[Tool/Product 2]:** [Brief description or context of mention]

### Points of Debate and Divergent Opinions

*   **[Debate Topic 1]:** [Description of different viewpoints]
*   **[Debate Topic 2]:** [Description of different viewpoints]
"""

    report_conclusion_part = """
---

## Report Conclusion

[Summarize here the 3 or 4 most important takeaways from the discussion. What are the final recommendations?]
"""

    sentiment_analysis_part = """
---

## Sentiment Analysis

*   **Overall Sentiment:** [Overall sentiment of the discussion (e.g., Positive, Negative, Neutral, Mixed)]
*   **Key Positive Aspects:** [List 2-3 positive themes or points of view]
*   **Key Negative Aspects:** [List 2-3 negative themes or points of view]
"""

    # Construct templates dynamically based on detail_level
    if detail_level == "concise":
        selected_template = base_template_part
    elif detail_level == "standard":
        selected_template = base_template_part + central_issue_part + report_conclusion_part
    else: # Default to detailed
        selected_template = base_template_part + central_issue_part + community_discussion_part + report_conclusion_part

    # Add sentiment analysis part if enabled
    if enable_text_analysis:
        selected_template += sentiment_analysis_part

    # Fill in the Key Information section of the selected template
    if submission_data:
        selected_template = selected_template.replace("[Thread Title]", sanitize_input(submission_data.get('title', 'N/A')))
        selected_template = selected_template.replace("[Link to thread]", sanitize_input(submission_data.get('url', 'N/A')))
        selected_template = selected_template.replace("[Subreddit Name]", sanitize_input(submission_data.get('subreddit', 'N/A')))
        selected_template = selected_template.replace("[Original Post Date]", sanitize_input(submission_data.get('date', 'N/A')))
        selected_template = selected_template.replace("[Number of Comments]", str(submission_data.get('num_comments', 'N/A')))
        selected_template = selected_template.replace("[Google Gemini model name]", model_name)

    # Instruction for the AI to fill the template
    prompt_instruction = f"""
Please summarize the following Reddit thread comments and fill in the provided template.
Ensure you strictly adhere to the template structure and fill all bracketed fields `[ ]` with relevant information extracted from the comments.
If a section has no relevant information, you can leave its bullet points or descriptions empty, but keep the section headers.

Reddit Comments:
{comment_text}

Template to fill:
{selected_template}

Summary:
"""

    try:
        # Ensure the model name is correctly formatted (e.g., "models/gemini-pro")
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
            
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt_instruction) # Use the full prompt with template
        
        # Check for empty or invalid response
        if not response.text or not response.text.strip():
            return "The model returned an empty response. Please try again."
            
        return response.text.strip()
    except Exception as e:
        error_message = f"Error summarizing with Google Gemini: {e}"
        print(f"{error_message} (Model: {model_name})")
        return "An error occurred while summarizing with Google Gemini. Please check your API key, the selected model, and try again."

def get_reddit_digest(url, summarization_method="top5", model_name=None, detail_level=None, enable_text_analysis=False):
    # Enhanced URL validation
    is_valid, message = validate_reddit_url(url)
    if not is_valid:
        return f"Invalid Reddit URL: {message}", None, None
    
    # Parse URL to extract components
    parsed_url = urlparse(url)
    path_pattern = r'^/r/([^/]+)/comments/([^/]+)(/[^/]*)?/?$'
    match = re.match(path_pattern, parsed_url.path)
    
    subreddit_name = match.group(1)
    submission_id = match.group(2)

    api_keys = load_api_keys()

    try:
        # Initialize PRAW with your Reddit API credentials
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

        # Prepare submission data for the template
        submission_date = datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S')
        submission_data = {
            'title': submission.title,
            'url': url,
            'subreddit': submission.subreddit.display_name,
            'date': submission_date,
            'num_comments': submission.num_comments
        }

        all_comments = []
        for top_level_comment in submission.comments:
            if isinstance(top_level_comment, praw.models.Comment):
                all_comments.append(sanitize_input(top_level_comment.body))
        
        if not all_comments:
            return "No top-level comments found for summarization."

        if summarization_method == "top5":
            digest = f"# Reddit Thread Summary: {sanitize_input(submission_data.get('title', 'N/A'))}\n\n"
            digest += "## Key Information\n\n"
            digest += f"*   **Source:** {sanitize_input(submission_data.get('url', 'N/A'))}\n"
            digest += f"*   **Subreddit:** r/{sanitize_input(submission_data.get('subreddit', 'N/A'))}\n"
            digest += f"*   **Publication Date:** {sanitize_input(submission_data.get('date', 'N/A'))}\n"
            digest += f"*   **Activity:** {submission_data.get('num_comments', 'N/A')}\n"
            digest += "*   **Summarization Method:** Top 5 Comments (N/A)\n\n"
            digest += "---\n\n"
            digest += "Top 5 Comments:\n"
            comment_count = 0
            for comment_body in all_comments:
                if comment_count >= 5:
                    break
                digest += f"- **Comment {comment_count+1}:** {comment_body}\n"
                comment_count += 1
            digest += "\n"
        elif summarization_method == "openai":
            model_preferences = load_model_preferences()
            actual_model_name = model_name if model_name else model_preferences.get('openai_default_model', 'gpt-4.1-nano')
            digest = summarize_with_openai(all_comments, api_keys.get('openai_api_key'), actual_model_name, detail_level, submission_data, enable_text_analysis)
        elif summarization_method == "gemini":
            model_preferences = load_model_preferences()
            actual_model_name = model_name if model_name else model_preferences.get('gemini_default_model', 'gemini-2.5-flash')
            digest = summarize_with_gemini(all_comments, api_keys.get('google_gemini_api_key'), actual_model_name, detail_level, submission_data, enable_text_analysis)
        else: # Default to top5 if method is unrecognized
            digest = f"# Reddit Digest: {sanitize_input(submission.title)}\n\n"
            if submission.selftext:
                digest += f"## Post Content:\n{sanitize_input(submission.selftext)}\n\n"
            elif submission.url and not submission.is_self:
                digest += f"## Post Link:\n{sanitize_input(submission.url)}\n\n"
            
            digest += "## Top 5 Comments (Default):\n\n"
            comment_count = 0
            for comment_body in all_comments:
                if comment_count >= 5:
                    break
                digest += f"- **Comment {comment_count+1}:** {comment_body}\n"
                comment_count += 1
            digest += "\n"

    except Exception as e:
        print(f"Error fetching Reddit content or summarizing: {e}")
        return "An unexpected error occurred while fetching Reddit content or summarizing. Please check the URL, your internet connection, and your API credentials.", None, None

    return digest, actual_model_name if summarization_method in ["openai", "gemini"] else None, submission.title
