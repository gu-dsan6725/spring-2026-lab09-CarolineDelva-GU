"""Dump all Mem0 cloud entries as raw JSON."""
import os
import json
import argparse
from dotenv import load_dotenv
from mem0 import MemoryClient

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Dump Mem0 cloud entries as raw JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump all users
  uv run python dump_mem0_entries.py

  # Dump specific user
  uv run python dump_mem0_entries.py --user-id alice

  # Save to custom file
  uv run python dump_mem0_entries.py --output custom_dump.json
"""
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Specific user_id to dump (default: all known users)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="mem0_dump.json",
        help="Output JSON file (default: mem0_dump.json)"
    )

    args = parser.parse_args()

    MEM0_API_KEY = os.getenv("MEM0_API_KEY")
    if not MEM0_API_KEY:
        print("ERROR: MEM0_API_KEY not found in environment")
        print("Get your free API key from https://app.mem0.ai/dashboard")
        exit(1)

    client = MemoryClient(api_key=MEM0_API_KEY)

    # Determine which users to query
    if args.user_id:
        users_to_query = [args.user_id]
        print(f"\n{'='*70}")
        print(f"Dumping Mem0 Entries for user_id: {args.user_id}")
        print("="*70 + "\n")
    else:
        # Query all known users
        users_to_query = [
            "demo_user",
            "alice",
            "carol"

        ]
        print(f"\n{'='*70}")
        print("Dumping ALL Mem0 Cloud Entries (all known users)")
        print("="*70 + "\n")

    all_entries = []

    # Get all users/runs from Mem0 to find run_ids
    print("Getting all runs from Mem0...")
    try:
        users_data = client.users()
        all_runs_info = users_data.get("results", [])
        print(f"  Total entities: {len(all_runs_info)}")
    except Exception as e:
        print(f"  Error getting users: {e}")
        all_runs_info = []

    for user_id in users_to_query:
        print(f"\nFetching memories for user_id: {user_id}...")

        # Find all run_ids for this user
        # Runs are typically named: user_id-session-N
        user_runs = [r["name"] for r in all_runs_info
                    if r.get("type") == "run" and r["name"].startswith(user_id + "-")]

        print(f"  Found {len(user_runs)} runs: {user_runs}")

        # Query memories from each run
        user_memories = []
        for run_id in user_runs:
            try:
                response = client.get_all(filters={"run_id": run_id})
                memories = response.get("results", [])

                # Always print the result for each run
                print(f"    Run '{run_id}': {len(memories)} memories")

                if memories:
                    for mem in memories:
                        mem["_queried_user_id"] = user_id  # Add for reference
                        mem["_queried_run_id"] = run_id  # Add run_id for reference
                        user_memories.append(mem)
            except Exception as e:
                print(f"    Run '{run_id}': Error - {e}")

        # Fallback: try direct user_id query (may not work but worth trying)
        if not user_memories:
            print(f"  Trying direct user_id query as fallback...")
            try:
                response = client.get_all(filters={"user_id": user_id})
                memories = response.get("results", [])
                if memories:
                    print(f"    Found {len(memories)} memories via user_id")
                    for mem in memories:
                        mem["_queried_user_id"] = user_id
                        user_memories.append(mem)
            except Exception as e:
                print(f"    Error: {e}")

        if user_memories:
            print(f"  Total: {len(user_memories)} memories for {user_id}")
            all_entries.extend(user_memories)
        else:
            print(f"  No memories found for {user_id}")

    print(f"\n{'='*70}")
    print(f"Total entries retrieved: {len(all_entries)}")
    print("="*70 + "\n")

    # Write to JSON file
    with open(args.output, "w") as f:
        json.dump(all_entries, f, indent=2, default=str)

    print(f"✓ Saved to {args.output}")

    # Also print to console for quick inspection
    print(f"\n{'='*70}")
    print(f"Sample entries (first 3):")
    print("="*70 + "\n")

    for i, entry in enumerate(all_entries[:3], 1):
        print(f"\nEntry {i}:")
        print(json.dumps(entry, indent=2, default=str))
        print()

    if len(all_entries) > 3:
        print(f"... and {len(all_entries) - 3} more entries")

    print(f"\n✓ Full dump available in: {args.output}\n")


if __name__ == "__main__":
    main()
