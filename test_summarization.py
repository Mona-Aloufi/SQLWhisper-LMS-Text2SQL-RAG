#!/usr/bin/env python3
"""
Test script for ResultSummarizationService
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.summarization_service import ResultSummarizationService

def test_basic_summarization():
    """Test basic summarization functionality"""
    print("=" * 70)
    print("Test 1: Basic Summarization")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    # Sample query results
    sample_results = [
        {"name": "Alice", "score": 95, "department": "Math"},
        {"name": "Bob", "score": 87, "department": "Science"},
        {"name": "Charlie", "score": 92, "department": "Math"},
        {"name": "Diana", "score": 88, "department": "Science"},
    ]
    
    question = "Show me all students with score greater than 80"
    sql_query = "SELECT name, score, department FROM students WHERE score > 80"
    
    print(f"\nQuestion: {question}")
    print(f"SQL: {sql_query}")
    print(f"Results: {len(sample_results)} rows")
    print("\nGenerating summary...\n")
    
    try:
        result = service.generate_summary(
            question=question,
            results=sample_results,
            sql_query=sql_query,
            max_rows=10
        )
        
        print("✅ Summary Generated Successfully")
        print(f"Summary Type: {result.get('summary_type', 'unknown')}")
        print(f"Row Count: {result.get('row_count', 0)}")
        print(f"Success: {result.get('success', False)}")
        print(f"\n{'='*70}")
        print("SUMMARY:")
        print("="*70)
        print(result.get('summary', 'No summary generated'))
        print("="*70)
        
        if result.get('confidence'):
            print(f"\nConfidence: {result.get('confidence', 0):.2%}")
        
        if result.get('raw_output'):
            print(f"\nRaw Output (first 300 chars):")
            print(result.get('raw_output', '')[:300] + "...")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_empty_results():
    """Test with empty results"""
    print("\n" + "=" * 70)
    print("Test 2: Empty Results Handling")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    result = service.generate_summary(
        question="Show me all students",
        results=[],
        sql_query="SELECT * FROM students"
    )
    
    print(f"Summary: {result.get('summary')}")
    print(f"Success: {result.get('success')}")
    print(f"Summary Type: {result.get('summary_type')}")
    
    success = result.get('success') and "No data" in result.get('summary', '')
    print("✅ PASS" if success else "❌ FAIL")
    return success

def test_large_dataset():
    """Test with larger dataset"""
    print("\n" + "=" * 70)
    print("Test 3: Large Dataset (Testing max_rows limit)")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    # Create larger dataset
    large_results = []
    for i in range(25):
        large_results.append({
            "id": i + 1,
            "product": f"Product_{i+1}",
            "price": 10.0 + i * 2.5,
            "category": "Electronics" if i % 2 == 0 else "Clothing"
        })
    
    question = "Show me all products"
    sql_query = "SELECT * FROM products"
    
    print(f"Total rows: {len(large_results)}")
    print(f"Max rows for summary: 20")
    print("\nGenerating summary...\n")
    
    try:
        result = service.generate_summary(
            question=question,
            results=large_results,
            sql_query=sql_query,
            max_rows=20
        )
        
        print("✅ Summary Generated")
        print(f"Row Count: {result.get('row_count')}")
        print(f"\nSummary:")
        print("-" * 70)
        print(result.get('summary', ''))
        print("-" * 70)
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_numeric_data():
    """Test with numeric/aggregate data"""
    print("\n" + "=" * 70)
    print("Test 4: Numeric Data Summary")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    # Sales data
    sales_results = [
        {"month": "January", "revenue": 50000, "orders": 120},
        {"month": "February", "revenue": 55000, "orders": 135},
        {"month": "March", "revenue": 60000, "orders": 150},
        {"month": "April", "revenue": 58000, "orders": 142},
    ]
    
    question = "What are the monthly sales figures?"
    sql_query = "SELECT month, revenue, orders FROM sales ORDER BY month"
    
    print(f"Question: {question}")
    print(f"Results: {len(sales_results)} rows")
    print("\nGenerating summary...\n")
    
    try:
        result = service.generate_summary(
            question=question,
            results=sales_results,
            sql_query=sql_query,
            max_rows=10
        )
        
        print("✅ Summary Generated")
        print(f"\nSummary:")
        print("-" * 70)
        print(result.get('summary', ''))
        print("-" * 70)
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_quick_insights():
    """Test quick insights generation"""
    print("\n" + "=" * 70)
    print("Test 5: Quick Insights")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    sample_results = [
        {"product": "Laptop", "sales": 150, "revenue": 150000},
        {"product": "Phone", "sales": 200, "revenue": 100000},
        {"product": "Tablet", "sales": 75, "revenue": 37500},
    ]
    
    insights = service.quick_insights(
        results=sample_results,
        question="Show me product sales"
    )
    
    print(f"Generated {len(insights)} insight(s):\n")
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")
    
    success = len(insights) > 0
    print("\n✅ PASS" if success else "❌ FAIL")
    return success

def test_fallback_summary():
    """Test fallback mechanism"""
    print("\n" + "=" * 70)
    print("Test 6: Fallback Summary")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    sample_results = [
        {"id": 1, "name": "Test"},
        {"id": 2, "name": "Test2"},
    ]
    
    result = service._generate_fallback_summary(
        results=sample_results,
        question="Test question"
    )
    
    print(f"Fallback Summary: {result.get('summary')}")
    print(f"Success: {result.get('success')}")
    print(f"Summary Type: {result.get('summary_type')}")
    
    success = result.get('success') and result.get('summary')
    print("✅ PASS" if success else "❌ FAIL")
    return success

def test_data_formatting():
    """Test data formatting for LLM"""
    print("\n" + "=" * 70)
    print("Test 7: Data Formatting")
    print("=" * 70)
    
    service = ResultSummarizationService()
    
    sample_results = [
        {"name": "Alice", "age": 25, "city": "New York"},
        {"name": "Bob", "age": 30, "city": "Boston"},
    ]
    
    formatted = service._format_results_for_llm(sample_results, max_rows=10)
    
    print("Formatted data for LLM:")
    print("-" * 70)
    print(formatted)
    print("-" * 70)
    
    # Check if formatting is correct
    has_columns = "Columns:" in formatted
    has_data = "Data:" in formatted
    has_rows = "Row" in formatted
    
    success = has_columns and has_data and has_rows
    print("\n✅ PASS" if success else "❌ FAIL")
    return success

if __name__ == "__main__":
    print("\n🧪 Testing ResultSummarizationService\n")
    print("Using model: google/flan-t5-base")
    print("=" * 70)
    
    results = []
    
    try:
        # Run all tests
        results.append(("Basic Summarization", test_basic_summarization()))
        results.append(("Empty Results", test_empty_results()))
        results.append(("Large Dataset", test_large_dataset()))
        results.append(("Numeric Data", test_numeric_data()))
        results.append(("Quick Insights", test_quick_insights()))
        results.append(("Fallback Summary", test_fallback_summary()))
        results.append(("Data Formatting", test_data_formatting()))
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        print("=" * 70)
        
        if passed == total:
            print("✅ All tests passed!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

