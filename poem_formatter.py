from openai import OpenAI

class PoemFormatter:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def format_poem(self, poem_data, idx=None):
        title = poem_data["Title"].strip()
        author = poem_data["Poet"].strip()
        poem = poem_data["Poem"]
        idx_str = f"Poem {idx}:" if idx is not None else ""
        header = f"--- {idx_str} {title} by {author} ---"
        
        # Check poem formatting using OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a formatter. If the input poem has proper poetic line breaks, output only 'True'. If it does not, output the poem with line breaks added in the proper, poetic places. Never output 'False'"},
                {"role": "user", "content": poem}
            ]
        )
        
        formatted_result = response.choices[0].message.content
        # final_poem = poem if formatted_result.strip().lower() == 'true' else f" ✨ {formatted_result}"

        if formatted_result.lower() == 'true':
            final_poem = f"{response.choices[0].message.content} \n {poem}"
        elif formatted_result.lower() == 'false':
            final_poem = f"WE'RE GETTING FASLE \n {poem}"
        else:
            final_poem = f"✨ {formatted_result}"

        
        print(f"\n{header}\n{final_poem}") 