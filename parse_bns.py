"""
Smart BNS text parser.
Splits each section into structured semantic chunks:
  - definition: The core legal definition of the offence
  - punishment: Imprisonment terms, fines
  - illustrations: Example scenarios (a), (b), (c)...
  - exceptions: When the section does NOT apply

This replaces the naive "one giant blob per section" approach.
"""

import re
import pandas as pd


def smart_chunk_section(raw_text):
    """
    Split a raw section description into semantic chunks.

    Returns dict with keys:
        definition, punishment, illustrations, exceptions
    """
    text = raw_text.strip()

    definition = ""
    punishment = ""
    illustrations = ""
    exceptions = ""

    # ── 1. Extract Illustrations ──
    illus_match = re.search(
        r'(?:Illustrations?\s*[.:\-—]|ILLUSTRATIONS?\s*[.:\-—])',
        text
    )
    if illus_match:
        illus_start = illus_match.start()
        # Everything from "Illustration" onward is illustrations
        illus_block = text[illus_start:]
        text = text[:illus_start].strip()

        # Check if there's an Exception block inside illustrations
        exc_in_illus = re.search(
            r'(?:Exceptions?\s*[.:\-—]|EXCEPTIONS?\s*[.:\-—])',
            illus_block
        )
        if exc_in_illus:
            illustrations = illus_block[:exc_in_illus.start()].strip()
            exceptions = illus_block[exc_in_illus.start():].strip()
        else:
            illustrations = illus_block.strip()

    # ── 2. Extract Exceptions (if not already found) ──
    if not exceptions:
        exc_match = re.search(
            r'(?:Exceptions?\s*[.:\-—]|EXCEPTIONS?\s*[.:\-—]|'
            r'Exception\s+\d|Except in the cases hereinafter excepted)',
            text
        )
        if exc_match:
            exceptions = text[exc_match.start():].strip()
            text = text[:exc_match.start()].strip()

    # ── 3. Extract Punishment ──
    # Look for punishment patterns
    punishment_patterns = [
        r'(?:shall be punished|shall be liable|punishable with|'
        r'be punished with|imprisonment.*(?:which may extend|not be less than)|'
        r'shall also be liable to fine)',
    ]

    # Find the sentence containing the punishment
    sentences = re.split(r'(?<=[.]) ', text)
    punishment_sentences = []
    definition_sentences = []

    for sent in sentences:
        is_punishment = False
        for pattern in punishment_patterns:
            if re.search(pattern, sent, re.IGNORECASE):
                is_punishment = True
                break
        if is_punishment:
            punishment_sentences.append(sent)
        else:
            definition_sentences.append(sent)

    if punishment_sentences:
        punishment = " ".join(punishment_sentences).strip()
        definition = " ".join(definition_sentences).strip()
    else:
        # No explicit punishment found — whole text is the definition
        definition = text.strip()

    # If definition is empty but we have text, use the original
    if not definition and text:
        definition = text.strip()

    return {
        "definition": definition,
        "punishment": punishment,
        "illustrations": illustrations,
        "exceptions": exceptions,
    }


def parse_bns_text(input_file, output_csv):
    """Parse raw BNS text into structured, smart-chunked CSV."""
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # ── Clean noise ──
    noise_patterns = [
        r"THE GAZETTE OF INDIA EXTRAORDINARY",
        r"PART II — Section 1",
        r"PUBLISHED BY AUTHORITY",
        r"MINISTRY OF LAW AND JUSTICE",
        r"\[Part II",
        r"No\. \d+\] NEW DELHI.*",
        r"CG-DL-E.*",
        r"Sec\. 1\]",
        r"_+",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # ── Extract sections ──
    section_pattern = re.compile(
        r'(\n\d{1,3}\.)\s+(.*?)(?=\n\d{1,3}\.|\\Z)', re.DOTALL
    )
    matches = section_pattern.findall(text)

    structured_data = []

    for match in matches:
        sec_num = match[0].strip().replace(".", "")
        content = match[1].strip()
        content = " ".join(content.split())  # normalize whitespace

        section_title = f"BNS Section {sec_num}"

        # Smart chunk the section
        chunks = smart_chunk_section(content)

        # Build the combined text for embedding (definition + punishment only)
        embed_text = chunks["definition"]
        if chunks["punishment"]:
            embed_text += " PUNISHMENT: " + chunks["punishment"]

        structured_data.append({
            'section': section_title,
            'description': embed_text,  # Clean text for embedding
            'definition': chunks["definition"],
            'punishment': chunks["punishment"],
            'illustrations': chunks["illustrations"],
            'exceptions': chunks["exceptions"],
            'full_text': content,  # Keep original for reference
            'pos_precedent': "Refer to BNS 2023 Commentary for latest rulings.",
            'neg_precedent': "No contradictory rulings recorded in this dataset.",
        })

    # ── Save to CSV ──
    if structured_data:
        df = pd.DataFrame(structured_data)
        df.to_csv(output_csv, index=False)
        print(f"Smart-chunked {len(df)} BNS sections into '{output_csv}'")

        # Stats
        has_punishment = sum(1 for d in structured_data if d['punishment'])
        has_illustrations = sum(1 for d in structured_data if d['illustrations'])
        has_exceptions = sum(1 for d in structured_data if d['exceptions'])
        avg_def_len = sum(len(d['definition']) for d in structured_data) / len(structured_data)

        print(f"  Sections with punishment clause: {has_punishment}")
        print(f"  Sections with illustrations: {has_illustrations}")
        print(f"  Sections with exceptions: {has_exceptions}")
        print(f"  Avg definition length: {avg_def_len:.0f} chars")
    else:
        print("No sections found. Check the raw text formatting.")


if __name__ == '__main__':
    parse_bns_text('raw_bns.txt', 'bns_laws.csv')