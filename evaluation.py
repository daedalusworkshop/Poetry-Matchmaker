import os
# Set environment variable to avoid tokenizer warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from openai import OpenAI
from config import OPENAI_API_KEY
import json

class PoetryEvaluator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    def llm_evaluate(self, prompt, poems):
        """Get LLM evaluation scores for poems matching a prompt."""
        scores = []
        for poem in poems:
            scores.append(self._evaluate_with_openai(prompt, poem))
        return scores

    def _evaluate_with_openai(self, prompt, poem):
        """Evaluate using GPT-4.1 with old system prompt and full poem text. Explanation is simple, direct, and connects qualia (prompt) to poem."""
        try:
            system_prompt = (
                "You are evaluating how well a poem matches a given prompt. "
                "Provide a score from 1.0 to 10.0 (decimals allowed, e.g. 9.3, 7.8) and a very simple, direct explanation (one or two sentences, plain language). "
                "Your explanation should connect the user's qualia (input) with the provided poem, but avoid literary jargon or elaborate phrasing. "
                "Format your response as JSON with keys 'score' and 'explanation'."
            )
            user_content = (
                f"Prompt (user qualia): {prompt}\n\n"
                f"Poem Title: {poem['title']}\nAuthor: {poem['author']}\n\nText:\n{poem['text']}"
            )
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            result = json.loads(response.choices[0].message.content)
            # Ensure score is float
            if 'score' in result:
                try:
                    result['score'] = float(result['score'])
                except:
                    pass
            return result
        except Exception as e:
            return {
                'score': 0.0,
                'explanation': f'Error with OpenAI evaluation: {str(e)}'
            }