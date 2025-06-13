from flask import Flask, request, jsonify
import re
import sqlparse
import os

app = Flask(__name__)

def normalize_quotes(query: str) -> str:
    """
    Replace curly single/double quotes and backticks with straight ASCII quotes.
    """
    replacements = {
        '\u2018': "'",  # LEFT SINGLE QUOTATION MARK
        '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK
        '\u201C': '"',  # LEFT DOUBLE QUOTATION MARK
        '\u201D': '"',  # RIGHT DOUBLE QUOTATION MARK
    }
    for old, new in replacements.items():
        query = query.replace(old, new)
    # Replace backticks (commonly misused for string literals) with single quotes.
    query = query.replace('`', "'")
    return query

def remove_numeric_quotes(query: str) -> str:
    """
    Remove quotes around pure numeric literals (integers or decimals, optional leading minus).
    E.g., '80000' -> 80000, '-3.14' -> -3.14.
    """
    pattern = re.compile(r'(["\'])(-?\d+(?:\.\d+)?)(\1)')
    return pattern.sub(lambda m: m.group(2), query)

def correct_and_format_sql(raw_query: str) -> str:
    """
    Normalize quotes, remove numeric quotes, then format with sqlparse.
    """
    normalized = normalize_quotes(raw_query)
    numeric_fixed = remove_numeric_quotes(normalized)
    try:
        formatted = sqlparse.format(numeric_fixed, reindent=True, keyword_case='upper')
    except Exception:
        formatted = numeric_fixed
    return formatted

@app.route('/correct_sql', methods=['GET', 'POST'])
def correct_sql():
    """
    Accepts:
      - GET:  ?query=<SQL string>
      - POST: JSON body {"query": "<SQL string>"} or form data query=<SQL string>
    Returns JSON: {"corrected_query": "<formatted SQL>"}
    """
    # Retrieve raw_query
    raw_query = ''
    if request.method == 'GET':
        raw_query = request.args.get('query', '') or ''
    else:
        data = request.get_json(silent=True)
        if data and 'query' in data:
            raw_query = data.get('query') or ''
        else:
            raw_query = request.form.get('query', '') or ''

    if not raw_query.strip():
        return jsonify({'error': 'No query provided'}), 400

    corrected = correct_and_format_sql(raw_query)
    return jsonify({'corrected_query': corrected})

if __name__ == '__main__':
    # For local testing: pick port from PORT env var or default 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
