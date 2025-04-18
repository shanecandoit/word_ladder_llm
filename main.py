import random

import ollama

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
5. Do not suggest a word already in the history list.
6. Do not use latex, nothing like: $\\boxed \\text .
Hints:
1. It should ideally be closer to the target word "{target_word}".
2. You may use valid neighbors, but you are not limited to them.
3. Consider what words you might use next turn.

Respond with some thoughts on the suggestion process, and then provide the suggested word.
Format:
<think>Thoughts on the suggestion process...</think>
Answer: "answer"
"""

dictionary_path = "words_alpha.txt"  # Path to your dictionary file
ollama_url = "http://localhost:11434"  # URL for the Ollama model
ollama_model = "deepseek-r1" # Name of the Ollama model
ollama_model = "gemma3:1b"


def is_neighbor(word1, word2):
    """
    Checks if two words are neighbors.

    Two words are neighbors if they have the same length and differ by exactly one letter.

    :param word1: The first word.
    :param word2: The second word.
    :return: True if the words are neighbors, False otherwise.
    """
    if len(word1) != len(word2):
        return False

    diff_count = 0
    for i in range(len(word1)):
        if word1[i] != word2[i]:
            diff_count += 1

    return diff_count == 1


def valid_word_neighbors(word, dictionary):
    """
    Finds all valid word neighbors for a given word.

    A valid neighbor is a word of the same length that differs by only one
    character and is present in the dictionary.

    :param word: The word to find neighbors for.
    :param dictionary: A set of valid words.
    :return: A list of valid word neighbors.
    """
    neighbors = []
    for i in range(len(word)):
        for char_code in range(ord('a'), ord('z') + 1):
            char = chr(char_code)
            new_word = word[:i] + char + word[i+1:]
            if new_word != word and new_word in dictionary:
                neighbors.append(new_word)
    return neighbors


def call_ollama_model(prompt_text):
    """
    Call the Ollama model with the provided prompt.

    :param prompt_text: The prompt text to send to the model.
    :return: The response from the model.
    """
    # Assuming you have a function to call your Ollama model
    try:
        # keep ollama inputs and outputs in utf-8
        # UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 5795: character maps to <undefined>
        prompt_text = prompt_text.encode('utf-8').decode('utf-8', errors='replace')
        # ollama.generate(model='llama3.2', prompt='Why is the sky blue?')
        response = ollama.generate(model=ollama_model, prompt=prompt_text)
        # print(f"Ollama response: {response}")
        """Ollama response: {'model': 'deepseek-r1', 
        'created_at': '2025-04-18T18:51:39.741907Z', 
        'response': '<think>\nOkay, so I\'m trying to figure out the next word in this word ladder game.
        """
        response_clean = response['response'].strip().encode('utf-8').decode('utf-8', errors='replace')
        return response_clean
    except Exception as e:
        print(f"Error calling Ollama model: {e}")
        return ""  # Return an empty string to avoid further errors


def remove_junk(text):
    """
    Remove unwanted characters from the text.

    :param text: The input text.
    :return: Cleaned text.
    """
    # Remove unwanted characters (e.g., LaTeX, HTML tags)
    junk = ['$', '/', '{', '}', '<', '>', '(', ')', '|', '**',]
    # it keeps wanting to boxed bold text, so remove those too
    junk += ['\\boxed', '\\bold', '\\text', '\\textbf', '\\textit', '\\texttt', '\\textcolor', '\\']
    for char in junk:
        text = text.replace(char, ' ')
    return text.strip()


def play_word_ladder_ollama(start_word, end_word, dictionary_path,
                            ollama_url, ollama_model, max_attempts=8):
    """
    Play the word ladder game using the Ollama model.
    """

    # Load the dictionary
    word_len = len(start_word)
    dictionary = set()
    with open(dictionary_path, 'r') as f:
        lines = f.readlines()
        # we only want words with the same length as the start word
        # and we want to ignore case
        for word in lines:
            word = word.strip().lower()
            if len(word) == word_len:
                dictionary.add(word)

    current_word = start_word.lower()
    target_word = end_word.lower()
    history_list = [current_word]

    # Check if the starting and target words are valid
    if current_word not in dictionary or target_word not in dictionary:
        print("Invalid starting or target word.")
        return

    for attempt in range(max_attempts):
        print(f"Attempt {attempt + 1}/{max_attempts}")
        print(f"Current word: {current_word}")
        print(f"Target word: {target_word}")
        print(f"History: {history_list}")

        # Get valid neighbors
        neighbors = valid_word_neighbors(current_word, dictionary)
        neighbors = [word for word in neighbors if word not in history_list]
        
        # too many neighbors?
        neighbor_limit = 20
        if len(neighbors) > neighbor_limit:
            # random shuffle the neighbors
            random.shuffle(neighbors)
            # limit the number of neighbors to the limit
            neighbors = neighbors[:neighbor_limit]

        # get the prompt ready
        history_str = ', '.join(history_list)
        word_len = len(current_word)
        prompt_text = prompt.format(current_word=current_word,
                                    target_word=target_word,
                                    history_str=history_str,
                                    word_len=word_len)

        # add the valid neighbors to the prompt
        prompt_text += "\nSome valid neighbors for inspiration: " + ', '.join(neighbors) + "\n\n"

        # show the prompt text
        print("\n\n---")
        print(f"Prompt text: {prompt_text}")
        print("---\n\n")

        # call the model
        model_response = call_ollama_model(prompt_text).strip().lower()
        model_response = model_response
        print(f"Model response: {model_response}")

        # Clean the response to remove junk characters
        model_response = remove_junk(model_response)
        print(f"Cleaned model response: {model_response}")

        # get just the suggested word from the response
        suggested_word = model_response.split('answer:')[-1].strip()
        suggested_word = suggested_word.lower()
        # is there a single word in the response?
        if ' ' in suggested_word:
            print("Multiple words found in the response. Taking the first one.")
            suggested_word = suggested_word.split()[0]
            # remove any punctuation
            suggested_word = ''.join(filter(str.isalpha, suggested_word))
        print(f"Suggested word: {suggested_word}")

        # is the suggested word a valid neighbor?
        is_valid = is_neighbor(suggested_word, current_word)
        if not is_valid:
            print(f"Suggested word '{suggested_word}' is not a valid neighbor of '{current_word}'.")
            print("Trying again...")
            continue

        # is the suggested word in the dictionary?
        if suggested_word not in dictionary:
            print(f"Suggested word '{suggested_word}' is not in the dictionary.")
            print("Trying again...")
            continue

        # update the current word and history list
        current_word = suggested_word
        history_list.append(current_word)

        # Check if we reached the target word
        if current_word == target_word:
            print("Congratulations! You've reached the target word.")
            print("GAME_WON! turn: ", attempt + 1)
            print("History: ", history_list)
            return
        else:
            print(f"Current word '{current_word}' is not the target word '{target_word}'.")
            print("Continuing to the next attempt...")

    print("Max attempts reached. Game over.")
    print("GAME_LOST! turn: ", attempt + 1)
    print("History: ", history_list)


if __name__ == "__main__":

    # Example usage
    start_word = "cold"
    end_word = "warm"
    print(f"Starting word: {start_word}")
    print(f"Target word: {end_word}")
    print(f"Dictionary path: {dictionary_path}")

    play_word_ladder_ollama(start_word, end_word, dictionary_path, ollama_url, ollama_model)
    print("Done.")
