#!/usr/bin/env python3
import csv
import re

class CollegeChatbot:
    def __init__(self, csv_path):
        self.colleges = self.load_data(csv_path)
        
    def load_data(self, csv_path):
        colleges = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                colleges.append({
                    'name': row.get('Institution Name_college', ''),
                    'state': row.get('State of Institution', ''),
                    'grad_rate': self.safe_float(row.get('Bachelor\'s Degree Graduation Rate Bachelor Degree Within 6 Years - Total')),
                    'net_price': self.safe_float(row.get('Average Net Price After Grants, 2020-21')),
                    'earnings': self.safe_float(row.get('Median Earnings of Students Working and Not Enrolled 10 Years After Entry')),
                    'gap': self.safe_float(row.get('Affordability Gap (net price minus income earned working 10 hrs at min wage)')),
                    'admission_rate': self.safe_float(row.get('Total Percent of Applicants Admitted'))
                })
        return [c for c in colleges if any([c['grad_rate'], c['net_price'], c['earnings']])]
    
    def safe_float(self, value):
        try:
            return float(value) if value and value.strip() and value != '.' else None
        except:
            return None
    
    def find_college(self, name):
        name_lower = name.lower()
        matches = [c for c in self.colleges if name_lower in c['name'].lower()]
        return matches[0] if matches else None
    
    def get_top_colleges(self, metric, n=5, reverse=True):
        filtered = [c for c in self.colleges if c[metric] is not None]
        return sorted(filtered, key=lambda x: x[metric], reverse=reverse)[:n]
    
    def format_college(self, college):
        return f"{college['name']} ({college['state']})"
    
    def respond(self, question):
        q = question.lower()
        
        # College lookup
        if 'tell me about' in q or 'information about' in q:
            college_name = re.search(r'about (.+)', q)
            if college_name:
                college = self.find_college(college_name.group(1))
                if college:
                    return f"{self.format_college(college)}\n" + \
                           f"Graduation Rate: {college['grad_rate']:.1f}% " if college['grad_rate'] else "N/A" + \
                           f"Net Price: ${college['net_price']:,.0f} " if college['net_price'] else "N/A" + \
                           f"Earnings: ${college['earnings']:,.0f}" if college['earnings'] else "N/A"
                return "College not found."
        
        # Best colleges queries
        if 'best' in q and 'graduation' in q:
            top = self.get_top_colleges('grad_rate', 3)
            return "Top colleges by graduation rate:\n" + \
                   "\n".join([f"{i+1}. {self.format_college(c)} - {c['grad_rate']:.1f}%" 
                             for i, c in enumerate(top)])
        
        if 'cheapest' in q or 'affordable' in q:
            top = self.get_top_colleges('net_price', 3, False)
            return "Most affordable colleges:\n" + \
                   "\n".join([f"{i+1}. {self.format_college(c)} - ${c['net_price']:,.0f}" 
                             for i, c in enumerate(top)])
        
        if 'highest earning' in q or 'best salary' in q:
            top = self.get_top_colleges('earnings', 3)
            return "Colleges with highest graduate earnings:\n" + \
                   "\n".join([f"{i+1}. {self.format_college(c)} - ${c['earnings']:,.0f}" 
                             for i, c in enumerate(top)])
        
        if 'best value' in q:
            top = self.get_top_colleges('gap', 3, False)
            return "Best value colleges (smallest affordability gap):\n" + \
                   "\n".join([f"{i+1}. {self.format_college(c)} - ${c['gap']:,.0f}" 
                             for i, c in enumerate(top)])
        
        # Compare colleges
        if 'compare' in q:
            colleges_mentioned = []
            for college in self.colleges:
                if college['name'].lower() in q:
                    colleges_mentioned.append(college)
            
            if len(colleges_mentioned) >= 2:
                result = "College Comparison:\n"
                for c in colleges_mentioned[:3]:
                    result += f"\n{self.format_college(c)}:\n"
                    result += f"  Graduation Rate: {c['grad_rate']:.1f}%\n" if c['grad_rate'] else "  Graduation Rate: N/A\n"
                    result += f"  Net Price: ${c['net_price']:,.0f}\n" if c['net_price'] else "  Net Price: N/A\n"
                    result += f"  Earnings: ${c['earnings']:,.0f}\n" if c['earnings'] else "  Earnings: N/A\n"
                return result
        
        return "I can help you with:\n" + \
               "- 'Tell me about [college name]'\n" + \
               "- 'What are the best colleges by graduation rate?'\n" + \
               "- 'What are the cheapest colleges?'\n" + \
               "- 'Which colleges have the highest earnings?'\n" + \
               "- 'What are the best value colleges?'\n" + \
               "- 'Compare [college1] and [college2]'"

def main():
    bot = CollegeChatbot('../fronted/data/merged_clean.csv')
    print("College Chatbot Ready! Ask me about colleges.")
    
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ['quit', 'exit', 'bye']:
            break
        print(f"Bot: {bot.respond(question)}")

if __name__ == "__main__":
    main()