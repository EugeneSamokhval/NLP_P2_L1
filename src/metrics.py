from typing import Sequence, Mapping, Tuple
import os


async def calculate_metrics(snippets: Sequence[Mapping[str, str]], query: str) -> Tuple[float, float, float, float, float]:
    a_f, b_f = set(), set()
    a = 0
    b = 0
    c = 0
    d = 0

    # Step 1: Analyze snippets returned from the MongoDB query
    for snippet in snippets:
        print(snippet)
        if 'raw_text' in snippet.keys():  # Assuming 'raw_text' contains the relevant text data
            text_snippets = snippet['raw_text']
            print(text_snippets)
            if query in text_snippets and snippet['filename'] not in a_f:
                a += 1
                a_f.add(snippet['filename'])
            if query not in text_snippets and snippet['filename'] not in b_f:
                b += 1
                b_f.add(snippet['filename'])

    # Step 2: Analyze the contents of files in the 'test' directory (optional if this step is necessary)
    for file_name in os.listdir(os.getcwd().removesuffix('src') + 'storage'):
        file_path = os.path.join(
            os.getcwd().removesuffix('src') + 'storage', file_name)
        print(file_path)
        if os.path.isfile(file_path):
            with open(file_path, "r") as file:
                content = file.read()
                if query in content and c < len(snippets):
                    c += 1
                if query not in content and d < len(snippets):
                    d += 1

    # Adjust values for c and d (difference between actual snippets returned and tested data)
    c, d = c - a, d - b

    # Step 3: Calculate metrics
    recall = a / (a + c) if a + c != 0 else 0
    precision = a / (a + b) if a + b != 0 else 0
    accuracy = (a + d) / (a + b + c + d)
    error = (b + c) / (a + b + c + d)
    f_measure = 2 / (1 / precision + 1 / recall) if precision and recall else 0

    # Step 4: Return the computed metrics
    with open('test_results.txt', 'w') as test_result:
        results = 'Recall:' + str(recall) + '\nPrecision:' + str(precision) + '\nAccuracy:' + str(
            accuracy) + '\nError:' + str(error) + '\nF_measure:' + str(f_measure)
        test_result.write(results)
