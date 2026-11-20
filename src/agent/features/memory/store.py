import re
import sqlite3


# ==========================================
# LONG-TERM MEMORY
# ==========================================


class MemoryStore:

    def __init__(self, db_path="memory.db"):

        self.db_path = db_path

        self.initialize_database()

    # --------------------------------------
    # CREATE DATABASE AND TABLE
    # --------------------------------------

    def initialize_database(self):

        with sqlite3.connect(self.db_path) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    fact TEXT NOT NULL UNIQUE COLLATE NOCASE,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                )
            """)

    # --------------------------------------
    # SAVE MEMORY
    # --------------------------------------

    def save(self, fact):

        fact = fact.strip()

        if not fact:
            return

        with sqlite3.connect(self.db_path) as conn:

            conn.execute(
                """
                INSERT OR IGNORE INTO memories (fact)
                VALUES (?)
                """,
                (fact,),
            )

    # --------------------------------------
    # GET ALL MEMORIES
    # --------------------------------------

    def get_all(self):

        with sqlite3.connect(self.db_path) as conn:

            rows = conn.execute("""
                SELECT id, fact, created_at
                FROM memories
                ORDER BY id
                """).fetchall()

        return rows

    # --------------------------------------
    # RETRIEVE RELEVANT MEMORIES
    # --------------------------------------

    def retrieve(self, query, limit=5):

        query_words = set(re.findall(r"\w+", query.lower()))

        stop_words = {
            "what",
            "who",
            "where",
            "when",
            "why",
            "how",
            "is",
            "am",
            "are",
            "the",
            "a",
            "an",
            "i",
            "my",
            "me",
            "do",
            "does",
            "did",
            "can",
            "you",
            "tell",
            "about",
            "please",
            "and",
            "or",
            "of",
            "to",
            "in",
            "on",
            "for",
            "it",
            "this",
            "that",
            "which",
            "using",
            "use",
        }

        query_words -= stop_words

        if not query_words:
            return []

        memories = self.get_all()

        ranked_memories = []

        for memory_id, fact, created_at in memories:

            fact_words = set(re.findall(r"\w+", fact.lower()))

            score = len(query_words.intersection(fact_words))

            if score > 0:

                ranked_memories.append((score, memory_id, fact))

        ranked_memories.sort(key=lambda item: item[0], reverse=True)

        # Return matching memories.
        if ranked_memories:

            return [fact for score, memory_id, fact in ranked_memories[:limit]]

        # Simple fallback:
        # If nothing matches, return recent memories.
        # This helps when the user uses different
        # words to refer to a previously saved fact.

        return [fact for memory_id, fact, created_at in memories[-limit:]]

    # --------------------------------------
    # DELETE MEMORY
    # --------------------------------------

    def delete(self, memory_id):

        with sqlite3.connect(self.db_path) as conn:

            conn.execute(
                """
                DELETE FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            )

    def find(self, keyword):

        with sqlite3.connect(self.db_path) as conn:

            cursor = conn.execute(
                """
                SELECT id, fact
                FROM memories
                WHERE fact LIKE ?
                """,
                (f"%{keyword}%",),
            )

            return cursor.fetchall()
