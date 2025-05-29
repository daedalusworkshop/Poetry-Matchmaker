import os
# Set environment variable to avoid tokenizer warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from openai import OpenAI
from poetry_db import PoetryDatabase
from config import OPENAI_API_KEY, DB_PATH
import pandas as pd
import json
from datetime import datetime

class PoetryEvaluator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.db = PoetryDatabase(DB_PATH)
        self.df = pd.read_csv("PoetryFoundationData.csv")
        # Create evaluation results directory if it doesn't exist
        self.results_dir = "evaluation_results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        
    def get_matches(self, prompt, n_results=3):
        """Get poem matches for a prompt"""
        results = self.db.query_poems(prompt, n_results=n_results)
        poems = []
        for poem_id in results["ids"][0]:
            poem_data = self.df.iloc[int(poem_id[4:])]
            poems.append({
                'title': poem_data['Title'].strip(),
                'author': poem_data['Poet'].strip(),
                'text': poem_data['Poem']
            })
        return poems

    def human_evaluate(self, prompt, poems):
        """Get human evaluation scores"""
        print(f"\n{'='*50}")
        print(f"Prompt: {prompt}\n")
        scores = []
        
        for i, poem in enumerate(poems):
            print(f"\nPoem {i+1}:")
            print(f"Title: {poem['title']}")
            print(f"Author: {poem['author']}")
            print(f"\n{poem['text']}\n")
            
            while True:
                try:
                    score = int(input("Your relevance score (1-10): "))
                    if 1 <= score <= 10:
                        break
                    print("Please enter a number between 1 and 10")
                except ValueError:
                    print("Please enter a valid number")
            
            notes = input("Optional notes about this match: ").strip()
            scores.append({
                'score': score,
                'notes': notes
            })
        
        return scores

    def llm_evaluate(self, prompt, poems):
        """Get LLM evaluation scores"""
        scores = []
        
        for poem in poems:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are evaluating how well a poem matches a given prompt. Provide a score from 1-10 and a brief ONE sentence explanation. Format your response as JSON with keys 'score' and 'explanation'."},
                    {"role": "user", "content": f"Prompt: {prompt}\n\nPoem Title: {poem['title']}\nAuthor: {poem['author']}\n\nText:\n{poem['text']}"}
                ]
            )
            try:
                result = json.loads(response.choices[0].message.content)
                scores.append(result)
            except:
                scores.append({
                    'score': 0,
                    'explanation': 'Error parsing LLM response'
                })
        
        return scores

    def run_evaluation(self, prompts, n_results=3):
        """Run full evaluation with both human and LLM scoring"""
        results = []
        
        for prompt in prompts:
            poems = self.get_matches(prompt, n_results)
            
            print("\nGetting your evaluation first...")
            human_scores = self.human_evaluate(prompt, poems)
            
            print("\nNow getting LLM evaluation...")
            llm_scores = self.llm_evaluate(prompt, poems)
            
            results.append({
                'prompt': prompt,
                'poems': poems,
                'human_scores': human_scores,
                'llm_scores': llm_scores
            })
            
            self.save_results(results)
            
        return results
    
    def save_results(self, results):
        """Save evaluation results to a file in the evaluation_results directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filepath}")

def main():
    evaluator = PoetryEvaluator()
    
    print("Welcome to Poetry Matchmaker Evaluation!")
    print("\nThis tool will help you evaluate the quality of poem matches.")
    print("You'll be shown poems matching your prompts and asked to rate them.")
    print("\nYou can enter multiple prompts. When you're done, just press Enter without typing anything.")
    
    prompts = []
    prompt_num = 1
    while True:
        prompt = input(f"\nPrompt #{prompt_num} (or press Enter to finish adding prompts): ").strip()
        if not prompt:
            if not prompts:
                print("\nUsing sample prompts...")
                prompts = [
                    "The bittersweet feeling of watching children grow up",
                    "Finding peace in nature during difficult times",
                    "The complexity of modern love"
                ]
            break
        prompts.append(prompt)
        prompt_num += 1
        print(f"Added prompt: '{prompt}'")
    
    print(f"\nEvaluating {len(prompts)} prompt(s)...")
    n_results = int(input("How many matches to evaluate per prompt? (default: 3) ") or 3)
    
    results = evaluator.run_evaluation(prompts, n_results)
    
    print("\nEvaluation complete! Results have been saved.")
    print("You can use these results to:")
    print("1. Compare your ratings with LLM ratings")
    print("2. Identify patterns in successful matches")
    print("3. Find areas where the matching could be improved")

if __name__ == "__main__":
    main()