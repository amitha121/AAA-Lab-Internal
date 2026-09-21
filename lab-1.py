# ============================================================
# EXP-1: TEXT-TO-SQL WORKFLOW
# Build an end-to-end LLM workflow with retrieval
# and query generation
# ============================================================

import sqlite3
from groq import Groq


# ============================================================
# 1. GROQ CONFIGURATION
# ============================================================

# Put your Groq API key here
GROQ_API_KEY = "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"

MODEL = "openai/gpt-oss-120b"

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# 2. CREATE SAMPLE DATABASE
# ============================================================

def create_database():

    conn = sqlite3.connect("company.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary INTEGER,
            experience INTEGER
        )
    """)

    # Check whether data already exists
    cursor.execute("""
        SELECT COUNT(*)
        FROM employees
    """)

    count = cursor.fetchone()[0]

    # Insert sample data only if table is empty
    if count == 0:

        employees = [
            (1, "Amitha", "Cyber Security", 65000, 1),
            (2, "Rahul", "IT", 72000, 3),
            (3, "Priya", "HR", 55000, 2),
            (4, "Arjun", "Cyber Security", 80000, 5),
            (5, "Sneha", "Finance", 68000, 4),
            (6, "Kiran", "IT", 60000, 2),
            (7, "Anjali", "Cyber Security", 75000, 3)
        ]

        cursor.executemany("""
            INSERT INTO employees
            VALUES (?, ?, ?, ?, ?)
        """, employees)

    conn.commit()

    return conn


# ============================================================
# 3. GET DATABASE SCHEMA
# ============================================================

def get_database_schema(conn):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
    """)

    tables = cursor.fetchall()

    schema = ""

    for table in tables:

        table_name = table[0]

        schema += f"\nTABLE: {table_name}\n"

        # Get columns
        cursor.execute(
            f"PRAGMA table_info({table_name})"
        )

        columns = cursor.fetchall()

        for column in columns:

            column_name = column[1]
            column_type = column[2]

            schema += (
                f"- {column_name} "
                f"({column_type})\n"
            )

        # Get sample records
        cursor.execute(
            f"SELECT * FROM {table_name} LIMIT 10"
        )

        rows = cursor.fetchall()

        if rows:

            schema += "\nSAMPLE DATA:\n"

            for row in rows:

                schema += f"{row}\n"

    return schema


# ============================================================
# 4. GROQ FUNCTION
# ============================================================

def ask_groq(prompt, temperature=0):

    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature
        )

        return response.choices[0].message.content.strip()

    except Exception as e:

        print("\nGroq API Error:")
        print(e)

        return None


# ============================================================
# 5. CLEAN GENERATED SQL
# ============================================================

def clean_sql(sql):

    if not sql:
        return ""

    # Remove markdown code blocks
    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")

    sql = sql.strip()

    # Remove "SQL:" if model adds it
    if sql.lower().startswith("sql:"):

        sql = sql[4:].strip()

    return sql


# ============================================================
# 6. SQL SECURITY VALIDATION
# ============================================================

def validate_sql(sql):

    if not sql:
        return False

    upper_sql = sql.upper().strip()

    # Only SELECT / WITH queries are allowed
    if not (
        upper_sql.startswith("SELECT")
        or upper_sql.startswith("WITH")
    ):
        return False

    dangerous_keywords = [
        "DROP ",
        "DELETE ",
        "UPDATE ",
        "INSERT ",
        "ALTER ",
        "TRUNCATE ",
        "CREATE ",
        "REPLACE "
    ]

    for keyword in dangerous_keywords:

        if keyword in upper_sql:

            return False

    return True


# ============================================================
# 7. MAIN TEXT-TO-SQL WORKFLOW
# ============================================================

def text_to_sql():

    print("\n")
    print("=" * 65)
    print("EXP-1: TEXT-TO-SQL WORKFLOW")
    print("=" * 65)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    conn = create_database()

    # --------------------------------------------------------
    # GET SCHEMA
    # --------------------------------------------------------

    schema = get_database_schema(conn)

    print("\nDATABASE SCHEMA")
    print("-" * 65)
    print(schema)

    # --------------------------------------------------------
    # USER QUESTION
    # --------------------------------------------------------

    question = input(
        "\nAsk a question about the database: "
    ).strip()

    if not question:

        print("\nQuestion cannot be empty.")

        conn.close()

        return

    # ========================================================
    # STEP 1: RETRIEVAL
    # ========================================================

    print("\n[1/4] Retrieving relevant schema...")

    retrieval_prompt = f"""
You are a database schema retrieval system.

USER QUESTION:
{question}

DATABASE SCHEMA AND SAMPLE DATA:
{schema}

Task:

Identify ONLY the tables, columns, and sample values
that are relevant to answering the user's question.

Important:
- Preserve the exact database values.
- Do not change spelling.
- Do not change capitalization.
- Do not remove spaces from text values.

For example:

"Cyber Security"

must remain exactly:

"Cyber Security"

Return only the relevant database information.
"""

    relevant_schema = ask_groq(
        retrieval_prompt,
        temperature=0
    )

    if not relevant_schema:

        conn.close()

        return

    print("\nRELEVANT SCHEMA")
    print("-" * 65)
    print(relevant_schema)

    # ========================================================
    # STEP 2: QUERY GENERATION
    # ========================================================

    print("\n[2/4] Generating SQL query...")

    sql_prompt = f"""
You are an expert SQLite SQL generator.

USER QUESTION:
{question}

RELEVANT DATABASE INFORMATION:
{relevant_schema}

Generate exactly ONE valid SQLite SQL query.

STRICT RULES:

1. Generate ONLY SELECT or WITH queries.
2. Never generate INSERT.
3. Never generate UPDATE.
4. Never generate DELETE.
5. Never generate DROP.
6. Never generate ALTER.
7. Never generate CREATE.
8. Use only tables and columns provided.
9. Match text values exactly as they appear
   in the database.
10. Preserve spaces and capitalization in text values.
11. Do not invent table names.
12. Do not invent column names.
13. Do not explain the query.
14. Do not use markdown.
15. Return ONLY the SQL query.

Example:

SELECT name
FROM employees
WHERE department = 'Cyber Security'
AND salary > 70000;
"""

    sql = ask_groq(
        sql_prompt,
        temperature=0
    )

    sql = clean_sql(sql)

    if not sql:

        print("\nSQL generation failed.")

        conn.close()

        return

    print("\nGENERATED SQL")
    print("-" * 65)
    print(sql)

    # ========================================================
    # STEP 3: VALIDATE AND EXECUTE SQL
    # ========================================================

    print("\n[3/4] Validating and executing SQL...")

    if not validate_sql(sql):

        print("\nUnsafe SQL detected.")
        print("Query execution blocked.")

        conn.close()

        return

    print("SQL validation: PASSED")

    try:

        cursor = conn.cursor()

        cursor.execute(sql)

        rows = cursor.fetchall()

        # Get column names
        if cursor.description:

            columns = [
                description[0]
                for description in cursor.description
            ]

        else:

            columns = []

        print("\nQUERY RESULT")
        print("-" * 65)

        print("Columns:", columns)

        if rows:

            for row in rows:

                print(row)

        else:

            print("No matching records found.")

    except Exception as e:

        print("\nSQL execution error:")
        print(e)

        conn.close()

        return

    # ========================================================
    # STEP 4: NATURAL LANGUAGE RESPONSE
    # ========================================================

    print("\n[4/4] Generating final answer...")

    answer_prompt = f"""
You are a data analyst.

USER QUESTION:
{question}

GENERATED SQL:
{sql}

DATABASE RESULT:

Columns:
{columns}

Rows:
{rows}

Answer the user's question using ONLY the database result.

Rules:

1. Do not invent information.
2. Do not change the database values.
3. If the result is empty, clearly say that
   no matching records were found.
4. Give a short, clear answer.
5. Do not mention the internal workflow.
"""

    answer = ask_groq(
        answer_prompt,
        temperature=0.2
    )

    if answer:

        print("\nFINAL ANSWER")
        print("=" * 65)
        print(answer)

    conn.close()


# ============================================================
# 8. PROGRAM START
# ============================================================

if __name__ == "__main__":

    if (
        not GROQ_API_KEY
        or
        GROQ_API_KEY == "Paste_your_Groq_API_key_here"
    ):

        print("\nERROR")
        print("-" * 65)
        print("Please add your Groq API key at the top of exp-1.py.")

    else:

        text_to_sql()