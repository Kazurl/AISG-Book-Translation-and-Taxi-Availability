import nltk
import os
from dotenv import load_dotenv
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer
from openai import OpenAI

load_dotenv()

SEALION_API_KEY = os.getenv("SEALION_API_KEY")
SEALION_API_URL = "https://api.sea-lion.ai/v1"
MAX_TOKENS = 128000

tokenizer = AutoTokenizer.from_pretrained("aisingapore/Gemma-SEA-LION-v4-27B-IT", trust_remote_code=True)

text = """
The Winepress
A short story by Josef Essberger

"You don't have to be French to enjoy a decent red wine," Charles Jousselin de Gruse used to tell his foreign guests whenever he entertained them in Paris. "But you do have to be French to recognize one," he would add with a laugh.

After a lifetime in the French diplomatic corps, the Count de Gruse lived with his wife in an elegant townhouse on Quai Voltaire. He was a likeable man, cultivated of course, with a well-deserved reputation as a generous host and an amusing raconteur.

This evening's guests were all European and all equally convinced that immigration was at the root of Europe's problems. Charles de Gruse said nothing. He had always concealed his contempt for such ideas. And, in any case, he had never much cared for these particular guests.

The first of the red Bordeaux was being served with the veal, and one of the guests turned to de Gruse.

"Come on, Charles, it's simple arithmetic. Nothing to do with race or colour. You must've had bags of experience of this sort of thing. What d'you say?"

"Yes, General. Bags!"

Without another word, de Gruse picked up his glass and introduced his bulbous, winey nose. After a moment he looked up with watery eyes.

"A truly full-bodied Bordeaux," he said warmly, "a wine among wines."

The four guests held their glasses to the light and studied their blood-red contents. They all agreed that it was the best wine they had ever tasted.

One by one the little white lights along the Seine were coming on, and from the first-floor windows you could see the brightly lit bateaux-mouches passing through the arches of the Pont du Carrousel. The party moved on to a dish of game served with a more vigorous claret.

"Can you imagine," asked de Gruse, as the claret was poured, "that there are people who actually serve wines they know nothing about?"

"Really?" said one of the guests, a German politician.

"Personally, before I uncork a bottle I like to know what's in it."

"But how? How can anyone be sure?"

"I like to hunt around the vineyards. Take this place I used to visit in Bordeaux. I got to know the winegrower there personally. That's the way to know what you're drinking."

"A matter of pedigree, Charles," said the other politician.

"This fellow," continued de Gruse as though the Dutchman had not spoken, "always gave you the story behind his wines. One of them was the most extraordinary story I ever heard. We were tasting, in his winery, and we came to a cask that made him frown. He asked if I agreed with him that red Bordeaux was the best wine in the world. Of course, I agreed. Then he made the strangest statement.

"'The wine in this cask,' he said, and there were tears in his eyes, 'is the best vintage in the world. But it started its life far from the country where it was grown.'"

De Gruse paused to check that his guests were being served.

"Well?" said the Dutchman.

De Gruse and his wife exchanged glances.

"Do tell them, mon chéri," she said.

De Gruse leaned forwards, took another sip of wine, and dabbed his lips with the corner of his napkin. This is the story he told them.
"""
nltk.download("punkt")
nltk.download("punkt_tab")


def chunk_by_tokens(text, max_tokens=MAX_TOKENS):
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

def smart_sentence_chunking(text, max_tokens=MAX_TOKENS):
    sentences = sent_tokenize(text)
    chunks, curr_chunk = [], ""
    for sent in sentences:
        temp_chunk = (curr_chunk + " " + sent).strip() if curr_chunk else sent
        # ensure this sentence doesn't exceed current chunk token limit
        if len(tokenizer.encode(temp_chunk)) <= max_tokens:
            curr_chunk = temp_chunk
        else:
            if curr_chunk:
                chunks.append(curr_chunk)
            curr_chunk = sent
    
    if curr_chunk:
        chunks.append(curr_chunk)
    return chunks

def translate_chunk(chunk: str, language: str):
    # todo: implement API call to SEA-LION
    client = OpenAI(
        api_key=SEALION_API_KEY,
        base_url=SEALION_API_URL
    )

    completion = client.chat.completions.create(
        model="aisingapore/Llama-SEA-LION-v3.5-70B-R",
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text from english to {language}. Return ONLY the most accurate translation in ${language}, without any explanation, alternatives, or romanization. Text: {chunk}"
            }
        ],
        extra_body={
            "chat_template_kwargs": {
                "thinking_mode": "off"
            }
        },
    )
    return completion.choices[0].message.content
output = translate_chunk(chunk_by_tokens(text), "chinese")
print(output)