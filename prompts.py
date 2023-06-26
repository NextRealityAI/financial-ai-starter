multi_task_prompt = """
Given some text, I want you to classify the question as either 'Stock Question', 'Earnings Summary', or 'Other'. Also list out any stock tickers for any relevant companies listed in the text. If the question is a Stock Question, return 1. If the question is an 'Earnings Summary' question, return 2. If the question is Other, return 3. 
 
Here is an example text and output: 
Text: What company is a competitor to Apple, Google, and Microsoft?
{"category": 1, "tickers": ["AAPL", "GOOGL", "MSFT"]}
Text: Why is the stock market going up? 
{"category": 3, "tickers": []}
Text: What were Tesla's latest earnings? 
{"category": 2, "tickers": ["TSLA"]]}
Text: What is an IRA? 
{"category": 3, "tickers": []}

Please provide the output in a valid JSON format shown above, with no other text. 
Here is the text to classify:
$PROMPT
"""

relevance_prompt = """
context: $CONTEXT

---

Is the text above related to this question: $QUESTION

Answer (yes or no). Answer YES or NO only.


###


"""

stock_question_template = '''
You are a stock expert answering questions. Using the following text, answer the following question."

Text:
"""
$CONTEXT
"""

Question:$QUESTION

Answer:
'''
