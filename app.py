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
    query = query.replace('`', "'")
    return query

def remove_numeric_quotes(query: str) -> str:
    """
    Remove quotes around pure numeric literals (integers or decimals, optional leading minus).
    """
    pattern = re.compile(r'(["\'])(-?\d+(?:\.\d+)?)(\1)')
    return pattern.sub(lambda m: m.group(2), query)

def correct_and_format_sql_single_line(raw_query: str) -> str:
    """
    Normalize quotes, remove numeric quotes, then format with sqlparse (uppercasing keywords),
    and finally collapse all whitespace/newlines into single spaces to produce a single-line SQL.
    """
    normalized = normalize_quotes(raw_query)
    numeric_fixed = remove_numeric_quotes(normalized)
    try:
        # Format without reindent (so sqlparse won't introduce newlines),
        # but uppercase keywords for consistency.
        formatted = sqlparse.format(numeric_fixed, keyword_case='upper', reindent=False)
    except Exception:
        formatted = numeric_fixed
    # Collapse all whitespace (including any newlines) into single spaces:
    # e.g. if sqlparse still inserted newlines or tabs, they’ll be normalized.
    single_line = re.sub(r'\s+', ' ', formatted).strip()
    return single_line

@app.route('/correct_sql', methods=['GET', 'POST'])
def correct_sql():
    """
    Accepts:
      - GET:  ?query=<SQL string>
      - POST: JSON body {"query": "<SQL string>"} or form data query=<SQL string>
    Returns JSON: {"corrected_query": "<single-line SQL>"}
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

    # Get single-line corrected SQL
    corrected_single_line = correct_and_format_sql_single_line(raw_query)
    return jsonify({'corrected_query': corrected_single_line})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
