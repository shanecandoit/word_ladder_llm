

prompt = """
You are playing a word ladder game.
The current word is "{current_word}".
The target word is "{target_word}".
The words used so far are: {history_str}.
Suggest the next valid English word in the ladder.
Rules:
1. The suggested word must be a real English word.
2. It must have the same length as "{current_word}" ({word_len} letters).
3. It must differ from "{current_word}" by exactly one letter.
4. It should ideally be closer to the target word "{target_word}".
5. Do not suggest a word already in the history list.
6. Do not use latex, nothing like: $\boxed{\text{zoom}}$.

Respond with some thoughts on the suggestion process, and then provide the suggested word.
Format:
<thoughts>Thoughts on the suggestion process...</thoughts>
Answer: <suggested_word>
"""

dictionary_path = "words_alpha.txt"  # Path to your dictionary file

import ollama

def ollama_model(prompt_text):
    """
    Call the Ollama model with the provided prompt.

    :param prompt_text: The prompt text to send to the model.
    :return: The response from the model.
    """
    # Assuming you have a function to call your Ollama model
    response = ollama.call(prompt_text)
    return response


def play_word_ladder_ollama(start_word, end_word, dictionary_path, ollama_url, ollama_model, max_attempts=5):
    """
    Play the word ladder game using the Ollama model.

    :param start_word: The starting word.
    :param end_word: The target word.
    :param dictionary_path: Path to the dictionary file.
    :param ollama_url: URL for the Ollama model.
    :param ollama_model: Name of the Ollama model to use.
    :param max_attempts: Maximum number of attempts to find a valid word.
    """

    # print the prompt for debugging
    print(f"Prompt: {prompt}")

    # Load the dictionary
    with open(dictionary_path, 'r') as f:
        dictionary = set(word.strip().lower() for word in f.readlines())

    current_word = start_word.lower()
    target_word = end_word.lower()
    history_list = [current_word]

    # Check if the starting and target words are valid
    if current_word not in dictionary or target_word not in dictionary:
        print("Invalid starting or target word.")
        return

    # Initialize Ollama model
    client = ollama.Client(host=ollama_url)
    print(f"client: {client}")

    for attempt in range(max_attempts):
        # Prepare values for the prompt
        history_str = ', '.join(history_list)
        word_len = len(current_word)
        # Generate prompt
        prompt_text = prompt.format(current_word=current_word, target_word=target_word, history_str=history_str, word_len=word_len)

        # Get suggestion from Ollama model
        response = client.generate(model=ollama_model, prompt=prompt_text)
        suggested_word = response['response'].strip().lower()

        if 'answer:' in suggested_word:
            suggested_word = suggested_word.split('answer:')[1].strip()
        elif '</thinking>' in suggested_word:
            suggested_word = suggested_word.split('</thinking>')[1].strip()
        else:
            suggested_word = suggested_word.splitlines()[-1].strip()
        print(f"Response from model: {suggested_word}")

        # Check if the suggested word is valid
        if (suggested_word in dictionary and
                len(suggested_word) == len(current_word) and
                sum(1 for a, b in zip(current_word, suggested_word) if a != b) == 1 and
                suggested_word not in history_list):
            print(f"Suggested word: {suggested_word}")
            history_list.append(suggested_word)
            current_word = suggested_word

            # Check if we reached the target word
            if current_word == target_word:
                print("Congratulations! You've reached the target word.")
                return
        else:
            print(f"Invalid suggestion: {suggested_word}.")

    print("Max attempts reached. Game over.")


if __name__ == "__main__":

    # Example usage
    start_word = "cold"
    end_word = "warm"
    print(f"Starting word: {start_word}")
    print(f"Target word: {end_word}")
    print(f"Dictionary path: {dictionary_path}")

    # dictionary_path is defined globally, no need to reassign here unless changing it.
    ollama_url = "http://localhost:11434"  # URL for the Ollama model
    ollama_model = "deepseek-r1:latest" # "llama2"  # Name of the Ollama model

    play_word_ladder_ollama(start_word, end_word, dictionary_path, ollama_url, ollama_model)
