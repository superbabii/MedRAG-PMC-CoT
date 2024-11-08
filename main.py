import json
import re
import random
import signal
from src.medrag import MedRAG

# Load the benchmark JSON file
with open('mmlu-med.json', 'r') as f:
    benchmark_data = json.load(f)

# Get all questions
all_questions = list(benchmark_data.items())

# all_questions = all_questions[:1000]

# Get random questions
all_questions = random.sample(list(benchmark_data.items()), 100)

# Initialize the MedRAG system
cot = MedRAG(llm_name="axiong/PMC_LLaMA_13B", rag=False)

# Store the results of comparisons
results = []
correct_count = 0
answered_questions = 0
number_all_questions = 0

# Define a timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Timeout occurred while generating answer.")

# Set the timeout limit to 60 seconds
signal.signal(signal.SIGALRM, timeout_handler)

# Function to extract the answer choice
def extract_answer_choice(generated_answer):
    # Map common answer words to corresponding option letters
    word_to_option = {
        "yes": "A",
        "no": "B",
        "maybe": "C"
    }

    # Check for "OPTION X IS CORRECT"
    option_correct_match = re.search(r"OPTION\s+([A-D])\s+IS\s+CORRECT", generated_answer, re.IGNORECASE)
    if option_correct_match:
        return option_correct_match.group(1).upper()

    # Check for "Answer: X" where X is a letter
    answer_letter_match = re.search(r"Answer:\s*([A-D])", generated_answer, re.IGNORECASE)
    if answer_letter_match:
        return answer_letter_match.group(1).upper()
    
    # Check for "The answer is choice X" where X is a letter
    choice_match = re.search(r"The answer is choice\s*([A-D])", generated_answer, re.IGNORECASE)
    if choice_match:
        return choice_match.group(1).upper()
    
    # Check for "The answer is choice X" where X is a letter
    choice_match = re.search(r"answer is\s*([A-D])", generated_answer, re.IGNORECASE)
    if choice_match:
        return choice_match.group(1).upper()
    
    # Check for "The answer is choice X" where X is a letter
    choice_match = re.search(r"The answer is option\s*([A-D])", generated_answer, re.IGNORECASE)
    if choice_match:
        return choice_match.group(1).upper()

    # Extract 'yes', 'no', or 'maybe' from the text, taking the last occurrence
    matches = re.findall(r"\b(yes|no|maybe)\b", generated_answer, re.IGNORECASE)
    if matches:
        last_answer_text = matches[-1].strip().lower()
        return word_to_option.get(last_answer_text)

    return None  # Return None if no valid option is found

# Iterate over each question and get the generated answer
for question_id, question_data in all_questions:
    # Extract the question, options, and correct answer
    question = question_data['question']
    options = question_data['options']
    correct_answer = question_data['answer']

    number_all_questions += 1
    # Use MedRAG to generate the answer with a timeout
    # signal.alarm(30)  # Set alarm for 60 seconds
    try:
        # Use MedRAG to generate the answer, considering shuffled robustness
        result = cot.medrag_answer(question_data=question_data, shuffle=True, num_shuffles=5)
        
        # Get the final consistent answer
        final_answer = result["answer"]
        frequency = result["frequency"]
        details = result["details"]

        # Print detailed debug information
        # print(f"Details of generated answers for question ID: {question_id}")
        # for i, (shuffled_options, mapped_answer, raw_answer) in enumerate(details):
        #     print(f"Shuffle {i + 1}:")
        #     print(f"Shuffled Options: {shuffled_options}")
        #     print(f"Mapped Answer: {mapped_answer}")
        #     print(f"Raw Answer: {raw_answer}")
        #     print('-' * 30)
        
        # print(f"Final_answer: {final_answer}")
        # Extract the generated answer choice
        # generated_choice = extract_answer_choice(final_answer)

        if not final_answer:
            print(f"No valid answer choice extracted for question ID: {question_id}")
            continue

        # Compare the generated answer with the correct one
        is_correct = correct_answer == final_answer
        if is_correct:
            correct_count += 1
        
        # answered_questions += 1
        
        # Calculate accuracy
        accuracy = correct_count / number_all_questions * 100 if number_all_questions > 0 else 0
        print(f"Generated Answer (Final Consistent): {final_answer}")
        print(f"Correct Answer: {correct_answer}")
        print(f"Frequency of Consistency: {frequency}")
        print(f"Is Correct: {is_correct}")
        print(f"Current Accuracy: {accuracy:.2f}%")
        print(f"All Questions: {number_all_questions}")
        print('-' * 50)

    except TimeoutException:
        print(f"Skipping question ID: {question_id} due to timeout.")
        continue