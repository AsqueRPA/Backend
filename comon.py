import re
import json

bruh = """Given the input dictionary `{2: 'Tostitos Chunky Salsa Medium 15.5 Oz'}`, to find the key with the closest value to 'Tostitos Chunky Salsa - Medium - 15.5 oz', let's break it down according to the criteria:

### Brand Name:
- **Tostitos** is present in the item name.
  - Score: 2

### Product Name:
- The product name **"Chunky Salsa"** is exactly correct.
  - Score: 3

### Flavor:
- The flavor **"Medium"** is exactly correct.
  - Score: 3

### Size:
- The size **"15.5 oz"** is exactly correct.
  - Score: 2

Adding up these scores: 2 (brand name) + 3 (product name) + 3 (flavor) + 2 (size) = 10

Given the criteria and calculations, the confidence level is 10 out of 10. The key that matches 'Tostitos Chunky Salsa - Medium - 15.5 oz' is 2, with a perfect match across all categories. 

Here's the output in the desired JSON format:

```json
{
  "key": "2",
  "confidence": "10",
  "reasoning": "The brand name, product name, flavor, and size all exactly match the criteria."
}
```
"""

import re
import json

def extract_json(message):
    # Normalize newlines and remove control characters except for tab
    normalized_message = re.sub(r'[\r\n]+', ' ', message)  # Replace newlines with spaces
    sanitized_message = re.sub(r'[^\x20-\x7E\t]', '', normalized_message)  # Remove non-printable chars

    # Attempt to find JSON starting and ending points without nested checks
    start = sanitized_message.find('{')
    end = sanitized_message.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        json_str = sanitized_message[start:end+1]
        # Make sure all single quotes are replaced with double quotes
        json_str = json_str.replace("'", '"')
        try:
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {}
    else:
        print("No JSON found in the message")
        return {}

# Test the function with the provided string
print(extract_json(bruh))
