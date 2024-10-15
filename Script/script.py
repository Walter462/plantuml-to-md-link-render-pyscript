import os
import re
import zlib
import base64

# Constants
# Deafult PlantUML srver address. Can be changed to local. Ex: http://localhost:8180/svg/
PLANTUML_BASE_URL = "https://www.plantuml.com/plantuml/svg/"
"""
Server adresses options:
WEB 1: https://kroki.io/plantuml/svg/
WEB 2: https://www.plantuml.com/plantuml/svg/
Local (on port 8180): http://localhost:8180/svg/
"""
PLANTUML_ENCODE_MAP = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'


def encode_chunk(chunk: bytes) -> str:
    """Encodes a 3-byte chunk into a 4-character string based on PlantUML's custom base64 encoding."""
    b1 = chunk[0] >> 2
    b2 = ((chunk[0] & 0x3) << 4) | (chunk[1] >> 4)
    b3 = ((chunk[1] & 0xF) << 2) | (chunk[2] >> 6)
    b4 = chunk[2] & 0x3F
    return PLANTUML_ENCODE_MAP[b1] + PLANTUML_ENCODE_MAP[b2] + PLANTUML_ENCODE_MAP[b3] + PLANTUML_ENCODE_MAP[b4]

def plantuml_encode(text: str) -> str:
    """Encodes the given PlantUML text into a URL-safe format using PlantUML's specific compression and encoding method."""
    compressed = zlib.compress(text.encode('utf-8'))[2:-4]  # remove zlib headers
    encoded = ''
    for i in range(0, len(compressed), 3):
        chunk = compressed[i:i + 3]
        chunk += b'\x00' * (3 - len(chunk))  # pad the chunk to 3 bytes if needed
        encoded += encode_chunk(chunk)
    return encoded.rstrip('A')  # remove padding


# combines BASE_URL with encoded PlantUML link
def generate_plantuml_url(uml_text: str) -> str:
    """Generates a PlantUML link from UML text using the correct PlantUML encoding."""
    encoded_text = plantuml_encode(uml_text)
    return PLANTUML_BASE_URL + encoded_text

def process_markdown_file(input_file: str, output_file: str, base_folder: str = None):
    """Processes the markdown file to detect PlantUML fenced code blocks and generate links."""
    if base_folder:
        input_file = os.path.join(base_folder, input_file)
        output_file = os.path.join(base_folder, output_file)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return
    except IOError as e:
        print(f"Error reading file '{input_file}': {e}")
        return

    # Step 1: Remove existing PlantUML links
    plantuml_link_pattern = re.compile(r'!\[\]\(https://www\.plantuml\.com/plantuml[^\)]*\)')
    #plantuml_link_pattern = re.compile(r'!\[\]\(https://www\.kroki\.io/plantuml[^\)]*\)')
    content_without_old_links = plantuml_link_pattern.sub('', content)

    # Step 2: Process PlantUML blocks to generate new links
    plantuml_block_pattern = re.compile(r'```plantuml\n(.*?)\n```', re.DOTALL)
    
    def replace_block_with_link(match):
        uml_text = match.group(1).strip()
        plantuml_link = generate_plantuml_url(uml_text)
        markdown_link = f"![]({plantuml_link})"
        return f"```plantuml\n{uml_text}\n```\n{markdown_link}"

    if not plantuml_block_pattern.search(content_without_old_links):
        print("No PlantUML blocks found.")
        return

    updated_content = plantuml_block_pattern.sub(replace_block_with_link, content_without_old_links)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated file saved as: {output_file}")
    except IOError as e:
        print(f"Error writing file '{output_file}': {e}")

# Script entry point
if __name__ == "__main__":
    project_dir = os.getcwd()
    data_folder = 'Tests'   # Change this to the name of your data folder
    file = "test_file.md"   # Change this to the name of your markdown file
    output_file = file

    # Start processing the markdown file
    process_markdown_file(file, output_file, os.path.join(project_dir, data_folder))
