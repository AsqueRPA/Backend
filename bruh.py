import re
import json

bruh = """Certainly, I can attempt to click on the link associated with "Saint Ze Yu". If the first attempt doesn't work as instructed, I will try clicking again.

Here is the action to click on the person labeled as '0':

```json
{"click": 31}
```

If this does not work, I will attempt to click again:

```json
{"click": 31}
```"""

def extract_json(message):
    # Adjusted regex to capture from the first '{' to the last '}'
    json_regex = r"\{[\s\S]*\}"
    matches = re.findall(json_regex, message)

    if matches:
        try:
            # Assuming the first match is the JSON we want
            json_data = json.loads(matches[0])
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {}
    else:
        print("No JSON found in the message")
        return {}
        
print(extract_json(bruh))