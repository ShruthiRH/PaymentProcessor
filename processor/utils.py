import random
import string

def generate_transcript_id(length=20):
    # Define the characters (letters and digits) to be used
    characters = string.ascii_letters + string.digits

    # Randomly choose characters to form the transcript ID
    transcript_id = ''.join(random.choice(characters) for _ in range(length))
    
    return transcript_id


