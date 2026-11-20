# ==========================================
# VIEW SAVED MEMORIES
# ==========================================


def view_memories(memory_store):

    memories = memory_store.get_all()

    print("\n========== SAVED LONG-TERM MEMORIES ==========")

    if not memories:

        print("No memories found.")

        return

    for memory_id, fact, created_at in memories:

        print(f"\nID: {memory_id}")

        print("FACT:", fact)

        print("CREATED:", created_at)
