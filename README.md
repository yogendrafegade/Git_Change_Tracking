🔍 Git Change Tracking 

🔹 Objective
The objective is to perform a Pre-Merge Audit. This allows a developer to see exactly what has been committed in a feature branch compared to the main branch before the actual merge happens. The final output is a structured JSON dictionary for easy data handling.

🚀 Key Features
•	Tree-to-Tree Comparison: Direct interaction with Git internals for high performance.
•	Smart Rename Detection: Uses find_similar() with a custom threshold (20%) to track files even when content is modified during a rename.
•	Binary Safety: Automatically handles non-text assets (images, PDFs) without crashing.
•	Structured JSON Output: Provides full file content in a format ready for web dashboards or APIs.

🛠️ Installation & Prerequisites
1. Requirements
•	Python: 3.11 or newer.
•	pip: Python package manager.
2. Setup (Windows Focused)
To install the high-performance Git library on Windows and avoid compilation errors, use:
Bash
pip install pygit2 --only-binary :all:
3. Verification
Bash
python -c "import pygit2; print(pygit2.__version__)"

⚙️ Implementation Details
1.	Repository Access: Uses pygit2.Repository(path) to interact directly with Git internals.
2.	Commit Detection: Uses revparse_single to turn branch names into actual Tree objects for comparison.
3.	Rename Logic: Implements diff.find_similar(flags=pygit2.GIT_DIFF_FIND_RENAMES, rename_threshold=20). This ensures that if a file is renamed and 80% of its code is changed, it is still tracked as a "Rename."
4.	Content Extraction:
o	Text Safelist: Only reads specific extensions (.py, .sql, .txt, .md, .json, .html, .css).
o	Binary Protection: Automatically identifies non-text files and replaces raw binary data with a [Binary/Non-Text Content Hidden] placeholder.
5.	JSON Construction: Serializes the results using json.dumps(output, indent=2) for a "Pretty Printed" report.
________________________________________
🧪 Test Scenarios Covered
•	Scenario 1 (Deletion): Identifies deleted files and preserves old_content.
•	Scenario 2 (New File): Identifies brand-new additions with new_content.
•	Scenario 3 (Binary/Image): Detects non-text files and hides raw binary data to prevent JSON bloat and ensure the script remains crash-proof.
•	Scenario 4 (Rename + Edit): Confirms that renaming with edits results in a single renamed status.
•	Scenario 5 (SQL Handling): Confirms multi-line SQL queries with special characters are preserved correctly.
•	Scenario 6 (Empty File): Confirms 0-byte files return empty strings rather than KeyErrors.
________________________________________
🛡️ Repository Protection (.gitignore)
To ensure security and keep the repository clean, the following files are excluded from version control:
•	Variable.py: Protects sensitive API tokens/credentials.
•	temp_pr_analysis/: Excludes the local workspace used for Git tree analysis.
•	__pycache__/: Ignores automatically generated Python bytecode.
•	.DS_Store / Thumbs.db: Ignores OS-specific metadata.
________________________________________
📄 Example JSON Output
JSON
{
  "changes": {
    "Hello_new.py": {
      "status": "renamed",
      "old_content": "print('Hello')",
      "new_content": "print('Hello Python World')"
    },
    "query.sql": {
      "status": "added",
      "old_content": "",
      "new_content": "SELECT * FROM employees WHERE id = 169;"
    }
  },
  "summary": {
    "comparison_type": "Mainbranch vs Feature",
    "total_files_changed": 2
  }
}

