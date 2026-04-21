#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qualcomm AI Assistant - Browser automation script
Asks questions to Qualcomm docs website AI Assistant via playwright-cli.

Usage:
    python ask_qualcomm_ai.py "What is IQ-9075?"
    python ask_qualcomm_ai.py "How to set up dev kit?" --product 1601111740076079 --timeout 60
"""

import subprocess
import sys
import json
import time
import re
import argparse

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def run_cmd(cmd, timeout=120):
    """Execute playwright-cli command and return stdout"""
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, shell=True,
        encoding='utf-8', errors='replace'
    )
    return result.stdout or "", result.stderr or "", result.returncode


def wait_for_ai_response(timeout=45, poll_interval=3):
    """Poll until AI finishes generating (Generating... disappears)"""
    elapsed = 0
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        stdout, _, _ = run_cmd("playwright-cli snapshot 2>&1")
        if "Generating..." in stdout:
            continue
        # Input box re-enabled means response complete
        if 'textbox "Ask a question"' in stdout:
            after = stdout.split('textbox "Ask a question"')[1].split('\n')[0]
            if '[disabled]' not in after:
                return True
        if "Was this" in stdout or "Feedback" in stdout:
            return True
    return False


def parse_answer_from_snapshot():
    """Get snapshot and parse AI reply text and source links"""
    stdout, _, _ = run_cmd("playwright-cli snapshot 2>&1")
    answer_parts = []
    sources = []
    capture = False
    capture_sources = False
    lines = stdout.split('\n')

    for i, line in enumerate(lines):
        # Start capturing after "Gen AI" marker or answer intro
        if ('Gen AI' in line or 'Let me provide' in line) and 'generic' in line.lower():
            capture = True
            continue

        # Sources section
        if 'text: Sources' in line:
            capture = False
            capture_sources = True
            continue

        # Feedback section - stop capturing
        if 'Was this' in line:
            capture = False
            capture_sources = False
            continue

        # Capture answer content
        if capture:
            m = re.search(r'- text:\s*(.+)', line)
            if m:
                text = m.group(1).strip().strip('"')
                text = re.sub(r'\s*"\d+"\s*$', '', text)
                if text:
                    answer_parts.append(text)
            elif re.search(r'- paragraph \[ref=\w+\]:\s*".*"', line):
                m = re.search(r'- paragraph \[ref=\w+\]:\s*"(.+)"', line)
                if m:
                    answer_parts.append(m.group(1))
            elif re.search(r'- listitem \[ref=\w+\]:\s*"?.*"?$', line) and '- link' not in line:
                m = re.search(r'- listitem \[ref=\w+\]:\s*"?([^"]+)"?\s*$', line)
                if m:
                    text = m.group(1).strip()
                    if text and len(text) > 5:
                        answer_parts.append(f"  - {text}")

        # Capture source links
        if capture_sources and '/url:' in line:
            m = re.search(r'/url:\s*(https?://\S+)', line)
            if m:
                sources.append(m.group(1))

    return '\n'.join(answer_parts), sources


def extract_response_fallback(stdout):
    """Fallback extraction method from snapshot text"""
    answer_lines = []
    sources = []
    in_answer = False
    in_sources = False

    for line in stdout.split('\n'):
        if '- paragraph [ref=' in line and any(kw in line for kw in [
            'IQ-', 'QCS', 'Qualcomm', 'Dragonwing', 'The IQ', 'Let me provide',
            'Based on', 'The Qualcomm', 'octa-core', 'TOPS', 'Adreno',
            'Hexagon', 'Kryo', 'system-on-chip', 'SoC', 'development kit', 'EVK'
        ]) and 'AI Assistant' not in line:
            in_answer = True

        if '- text: Sources' in line:
            in_answer = False
            in_sources = True

        if in_sources and '- /url:' in line:
            url_match = re.search(r'/url:\s*(https?://[^\s]+)', line)
            if url_match:
                sources.append(url_match.group(1))

        if in_answer:
            text_match = re.search(r'- text:\s*(.+?)(?:\s*$)', line)
            if text_match:
                answer_lines.append(text_match.group(1).strip('"'))
            elif '- paragraph [ref=' in line:
                para_match = re.search(r'- paragraph \[ref=\w+\]:\s*(.+)', line)
                if para_match:
                    answer_lines.append(para_match.group(1).strip('"'))
            elif '- listitem [ref=' in line and '- text:' not in line:
                item_match = re.search(r'- listitem \[ref=\w+\]:\s*(.+)', line)
                if item_match:
                    answer_lines.append(f"  - {item_match.group(1).strip('\"')}")

    return '\n'.join(answer_lines), sources


def ask_qualcomm_ai(question, product_id="1601111740076079", timeout=45):
    """Main function: ask Qualcomm AI Assistant a question"""
    url = f"https://docs.qualcomm.com/nav/home?product={product_id}"

    log = lambda msg: print(f"[QA] {msg}", file=sys.stderr)

    log(f"Opening Qualcomm docs: {url}")

    # Step 1: Open browser
    stdout, stderr, rc = run_cmd(f'playwright-cli open --browser=msedge "{url}"', timeout=30)
    if rc != 0:
        log(f"ERROR: Failed to open browser: {stderr}")
        return {"error": "Failed to open browser", "details": stderr}

    # Step 2: Wait for page + AI Assistant to load
    log("Waiting for AI Assistant to load...")
    time.sleep(5)

    stdout, _, _ = run_cmd("playwright-cli snapshot 2>&1")
    if "Ask a question" not in stdout:
        log("AI Assistant not visible yet, waiting more...")
        time.sleep(5)
        stdout, _, _ = run_cmd("playwright-cli snapshot 2>&1")
        if "Ask a question" not in stdout:
            log("ERROR: AI Assistant not found on page")
            run_cmd("playwright-cli close")
            return {"error": "AI Assistant not found on page"}

    # Step 3: Start new chat
    if "Start a new chat" in stdout:
        log("Starting new chat...")
        run_cmd("playwright-cli click e110")
        time.sleep(2)

    # Step 4: Find input textbox ref
    stdout, _, _ = run_cmd("playwright-cli snapshot 2>&1")
    input_ref = "e134"  # default
    m = re.search(r'textbox "Ask a question"\s*(?:\[disabled\]\s*)?\[ref=(\w+)\]', stdout)
    if m:
        input_ref = m.group(1)
    log(f"Input box ref: {input_ref}")

    # Step 5: Fill question
    safe_question = question.replace('"', '\\"')
    log(f"Typing question: {question}")
    stdout, stderr, rc = run_cmd(f'playwright-cli fill {input_ref} "{safe_question}"', timeout=10)
    if rc != 0:
        log(f"ERROR: Failed to fill question: {stderr}")
        run_cmd("playwright-cli close")
        return {"error": "Failed to fill question"}

    # Step 6: Send
    log("Sending question (Enter)...")
    run_cmd("playwright-cli press Enter")

    # Step 7: Wait for response
    log(f"Waiting for AI reply (max {timeout}s)...")
    success = wait_for_ai_response(timeout=timeout)
    if not success:
        log("Timeout reached, trying to extract anyway...")
    time.sleep(3)

    # Step 8: Extract response
    log("Extracting reply...")
    answer, sources = parse_answer_from_snapshot()

    if not answer.strip():
        log("Using fallback extraction...")
        stdout, _, _ = run_cmd("playwright-cli snapshot 2>&1")
        answer, sources = extract_response_fallback(stdout)

    # Step 9: Close browser
    log("Closing browser...")
    run_cmd("playwright-cli close")

    result = {
        "question": question,
        "answer": answer.strip(),
        "sources": sources,
        "product_url": url,
        "status": "success" if answer.strip() else "empty_response"
    }
    return result


def format_output(result):
    """Format result as readable Markdown"""
    if "error" in result:
        return f"## ERROR\n\n{result['error']}\n\n{result.get('details', '')}"

    output = []
    output.append(f"## Question\n\n{result['question']}\n")
    output.append(f"## AI Reply\n\n{result['answer']}\n")

    if result['sources']:
        output.append("## Sources\n")
        for i, src in enumerate(result['sources'], 1):
            output.append(f"{i}. {src}")
        output.append("")

    output.append(f"*Source: {result['product_url']}*")
    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description="Ask Qualcomm AI Assistant a question")
    parser.add_argument("question", help="Question to ask")
    parser.add_argument("--product", default="1601111740076079",
                        help="Product ID (default: IQ-9075)")
    parser.add_argument("--timeout", type=int, default=45,
                        help="Max wait time for reply in seconds (default: 45)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Save output to file")

    args = parser.parse_args()
    result = ask_qualcomm_ai(args.question, args.product, args.timeout)

    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_output(result)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"[QA] Result saved to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
