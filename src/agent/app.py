from agent.features.chat import AgentSession, run_agent
from agent.features.memory import MemoryStore, view_memories
from agent.features.planning import execute_plan


# ==========================================
# MAIN PROGRAM
# ==========================================


def main():

    # CREATE ONE SHORT-TERM SESSION

    session = AgentSession()

    # CREATE ONE LONG-TERM MEMORY STORE

    memory_store = MemoryStore()

    while True:

        print("\n========== AI RESEARCH AGENT ==========")

        print("1. Direct agent execution")

        print("2. Planned agent execution")

        print("3. View saved long-term memories")

        print("4. Clear short-term conversation")

        print("5. Exit")

        choice = input("\nChoose an option: ").strip()

        # ----------------------------------
        # DIRECT EXECUTION
        # ----------------------------------

        if choice == "1":

            user_request = input("\nEnter your request: ")

            try:

                answer = run_agent(user_request, session, memory_store)

                print("\n========== FINAL ANSWER ==========")

                print(answer)

            except Exception as e:

                print("\nAGENT ERROR:", e)

        # ----------------------------------
        # PLANNED EXECUTION
        # ----------------------------------

        elif choice == "2":

            user_request = input("\nEnter your request: ")

            try:

                results, status = execute_plan(user_request, session, memory_store)

                print("\n========== FINAL TASK RESULTS ==========")

                for item in results:

                    print("\nTASK:", item["task"])

                    print("RESULT:", item["result"])

                print("\n========== FINAL PLAN STATUS ==========")

                for item in status:

                    print(f"{item['status'].upper()}: " f"{item['task']}")

            except Exception as e:

                print("\nPLANNING ERROR:", e)

        # ----------------------------------
        # VIEW LONG-TERM MEMORIES
        # ----------------------------------

        elif choice == "3":

            view_memories(memory_store)

        # ----------------------------------
        # CLEAR SHORT-TERM MEMORY
        # ----------------------------------

        elif choice == "4":

            session.clear()

            print("\nShort-term conversation history cleared.")

            print("Long-term memories remain saved.")

        # ----------------------------------
        # EXIT
        # ----------------------------------

        elif choice == "5":

            print("\nExiting AI agent. Goodbye!")

            break

        else:

            print("\nInvalid choice. Please select 1-5.")


# ==========================================
# PROGRAM ENTRY POINT
# ==========================================

if __name__ == "__main__":

    main()
