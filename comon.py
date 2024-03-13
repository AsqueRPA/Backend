import re
import json

bruh = """{
  "confidence": "6",
  "reasoning": "The item shown is 'Cheetos Mac'N Cheese Pasta With Flavored Sauce Flamin' Hot Flavor 2.11 Oz'. Here's the breakdown of the confidence score:

  - The brand name 'Cheetos' is present in the item name (2 points).
  - The product name is close. The correct product is 'Cheetos Mac'N Cheese - Bold & Cheesy', and this item is 'Cheetos Mac'N Cheese...Flamin' Hot Flavor', so the main product name is close, but the flavor is off (1 point for closeness of product name).
  - The flavor is not exactly correct; we are looking for 'Bold & Cheesy,' not 'Flamin' Hot' (0 points for flavor accuracy).
  - The size is exactly correct (2 points for size accuracy).
  - The packaging seems correct, based on what's standard for this type of product, so we will assume it's correct (1 point for packaging).

  Adding these up, we get a total confidence score of 6 out of a possible 10 points."
}
"""

def extract_json(message):
    # Normalize newlines and remove control characters except for tab
    normalized_message = re.sub(r'[\r\n]+', ' ', message)  # Replace newlines with spaces
    sanitized_message = re.sub(r'[^\x20-\x7E\t]', '', normalized_message)  # Remove non-printable chars

    json_regex = r"\{[\s\S]*?\}"  # Non-greedy match for content inside braces
    matches = re.findall(json_regex, sanitized_message)

    if matches:
        for match in matches:
            try:
                json_data = json.loads(match)
                return json_data  # Return the first valid JSON object
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        print("Valid JSON not found in the matches")
        return {}
    else:
        print("No JSON found in the message")
        return {}

    
print(extract_json(bruh))