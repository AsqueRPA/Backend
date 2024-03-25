import json
import re
def extract_full_json_objects(text):
    # Normalize newlines and remove control characters except for tab
    normalized_message = re.sub(r"[\r\n]+", " ", text)  # Replace newlines with spaces
    sanitized_message = re.sub(r"[^\x20-\x7E\t]", "", normalized_message)  # Remove non-printable chars

    json_objects = []
    stack = []  # Stack to keep track of braces
    start_index = None  # Start index of a JSON object

    # Iterate through the message to find JSON structures
    for i, char in enumerate(sanitized_message):
        if char == '{':
            stack.append('{')
            if start_index is None:
                start_index = i  # Mark the start of a potential JSON object
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:  # If stack is empty, we found a complete JSON object
                    try:
                        json_str = sanitized_message[start_index:i+1]  # Extract the JSON string
                        json_data = json.loads(json_str)  # Convert string to JSON
                        json_objects.append(json_data)  # Add to our list
                        start_index = None  # Reset start index for the next JSON object
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                        start_index = None  # Reset start index if decoding fails

    return json_objects

# Test the function
text = """Your previous message here. Let's type the follow-up message: {"input": {"select": 31, "text": "Hi Lucas, I just wanted to follow up on my previous message. I'm really keen to understand what challenges you're facing in scaling your growth. Could you share what's been the biggest hurdle for you lately?"}}"""

bruh = extract_full_json_objects(text)
for lmfao in bruh:
    print(lmfao["input"])
