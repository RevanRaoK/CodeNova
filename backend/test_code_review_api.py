"""
Test script for the code review API endpoints with multiple file uploads.

This script tests the /code-review endpoint to ensure it can handle
multiple file uploads and perform code analysis.
"""

import asyncio
import httpx
import json
from pathlib import Path

# Test files content
TEST_FILES = {
    "test1.py": """
def calculate_sum(a, b):
    # This function adds two numbers
    result = a + b
    return result

def main():
    x = 5
    y = 10
    total = calculate_sum(x, y)
    print(f"The sum is: {total}")

if __name__ == "__main__":
    main()
""",
    "test2.js": """
function calculateProduct(a, b) {
    // This function multiplies two numbers
    var result = a * b;
    return result;
}

function main() {
    var x = 5;
    var y = 10;
    var product = calculateProduct(x, y);
    console.log("The product is: " + product);
}

main();
""",
    "test3.java": """
public class Calculator {
    public static int calculateDifference(int a, int b) {
        // This method subtracts two numbers
        int result = a - b;
        return result;
    }
    
    public static void main(String[] args) {
        int x = 10;
        int y = 3;
        int difference = calculateDifference(x, y);
        System.out.println("T