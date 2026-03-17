#!/bin/bash
# Quick test script to verify the agent works

echo "Testing agent setup..."
echo ""

# Run a simple test
echo "What is Python?" | timeout 60 uv run python agent.py

echo ""
echo "Test complete! Check Braintrust dashboard for traces."
