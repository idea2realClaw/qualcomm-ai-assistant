# Qualcomm AI Assistant Skill

A [WorkBuddy](https://www.codebuddy.cn) Skill that uses browser automation to ask questions to the **Qualcomm Documentation AI Assistant** and retrieve answers based on official Qualcomm documentation.

## Features

- Ask natural language questions about Qualcomm products (IQ-9075, QCS6490, etc.)
- Get answers sourced from official Qualcomm documentation
- Extract referenced document links from AI responses
- Support for different Qualcomm product pages
- Structured JSON output mode

## Prerequisites

1. **Node.js** (for playwright-cli)
   ```bash
   npm install -g @playwright/cli
   ```

2. **Microsoft Edge** browser (or Chrome)

3. **Python 3.8+**

## Installation

Copy this skill to your WorkBuddy skills directory:
```bash
# User-level installation
cp -r qualcomm-ai-assistant ~/.workbuddy/skills/
```

## Usage

### Command Line
```bash
# Basic usage (default product: IQ-9075)
python scripts/ask_qualcomm_ai.py "What is IQ-9075?"

# With options
python scripts/ask_qualcomm_ai.py "How to set up dev kit?" --timeout 60 --json

# Different product
python scripts/ask_qualcomm_ai.py "QCS6490 specs" --product 1601111740076079

# Save output to file
python scripts/ask_qualcomm_ai.py "NPU TOPS" -o result.md
```

### As WorkBuddy Skill

The skill is triggered by phrases like:
- "Ask Qualcomm AI about..."
- "Qualcomm documentation..."
- "QCS6490 specifications"
- "IQ-9075 features"

## How It Works

1. Opens Qualcomm documentation website using `playwright-cli` + Edge browser
2. Locates the AI Assistant chat input box via accessibility snapshot
3. Types the question and sends via Enter key
4. Polls for response completion (waits for "Generating..." to disappear)
5. Extracts AI reply text and reference document links from page snapshot
6. Closes browser and returns structured result

## Supported Products

| Product | ID |
|---------|-----|
| IQ-9075 | 1601111740076079 |
| QCS6490 | Use `--product` flag with the correct product ID |

## Output Formats

### Default (Markdown)
```
## Question
What is IQ-9075?

## AI Reply
IQ-9075 is a Qualcomm Dragonwing processor...

## Sources
1. [Document Title](url)
2. [Document Title](url)
```

### JSON (`--json` flag)
```json
{
  "question": "...",
  "answer": "...",
  "sources": ["url1", "url2"],
  "product_url": "..."
}
```

## Configuration

The script uses `playwright-cli.json` in the working directory:
```json
{
  "snapshotOutput": "stdout"
}
```

## Known Limitations

- Requires a display/browser environment (no headless mode)
- Response time varies (15-60 seconds depending on question complexity)
- Input box element reference changes dynamically — the script handles this via regex matching on snapshot

## License

MIT License - see [LICENSE](LICENSE) for details.
