import os

# Define paths
output_path = r"c:\Users\Pinaka\Music\Chatbot\velome_chat\data\knowledge_base.md"
input_files = [
    r"c:\Users\Pinaka\Music\Chatbot\Important stuff.md",
    r"c:\Users\Pinaka\Music\Chatbot\data.md",
    r"c:\Users\Pinaka\Music\Chatbot\weird.md"
]

print(f"Merging files into {output_path}...")

merged_content = ""

for file_path in input_files:
    if os.path.exists(file_path):
        print(f"Reading {file_path}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                merged_content += f"\n\n--- SOURCE: {os.path.basename(file_path)} ---\n\n"
                merged_content += content
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    else:
        print(f"WARNING: File not found: {file_path}")

try:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(merged_content)
    print("Merge complete.")
except Exception as e:
    print(f"Error writing to output file: {e}")
