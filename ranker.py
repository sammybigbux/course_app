import pandas as pd
import numpy as np

class Ranker:
    """
    Class to recommend services based on user input, review scores, and budget 
    """
    def __init__(self, budget, user_auto_scores_raw, user_quality_scores_raw, copilot):
        quality_scores = [2, 3, 9, 5, 9.5, 7, 8, 8, 9, 1, 1]
        auto_scores = [7, 5, 8, 7, 7, 9, 9.5, 8, 10, 10, 10]
        services = [
                    "AI Assistants", 
                    "Copilot (PowerPoint)", 
                    "Beautiful AI", 
                    "Copilot (Word)",
                    "Grammarly",
                    "Trevor AI",
                    "Motion",
                    "Krisp",
                    "Otter",
                    "Zapier (2-step)",
                    "Zapier (multi-step)"
                ]
        copilot_list = ["Copilot for PowerPoint", "Writing with Copilot"]

        tasks = ["Reading texts", "PowerPoint", "PowerPoint", "Writing", "Writing", "Scheduling", "Scheduling", "Meetings", "Meetings", "Web apps", "Web apps"]
        user_auto_scores = [x for x in user_auto_scores_raw for _ in range(2)][1:]
        user_quality_scores = [x for x in user_quality_scores_raw for _ in range(2)][1:]
        assert len(services) == len(user_auto_scores), f"{len(user_auto_scores)}!={len(services)}"
        assert len(services) == len(user_quality_scores), f"{len(user_quality_scores)}!={len(services)}" 
        prices = [0, 0, 12, 0, 12, 0, 19, 0, 8, 0, 20]
        self.budget = budget
        assert self.budget is not None, "Budget is missing"
        self.data = pd.DataFrame({"service": services, "user_auto_score": user_auto_scores, "user_quality_score": user_quality_scores, "auto_score": auto_scores, "quality_score": quality_scores, "price": prices, "task": tasks})

        if not copilot:
            self.data = self.data[~self.data['service'].isin(copilot_list)]
    
    def rank(self):
        self.data['automation_stat'] = self.data['auto_score'] * 0.1 * self.data['user_auto_score']
        self.data['quality_stat'] = self.data['quality_score'] * 0.1 * self.data['user_quality_score']
        self.data['cost_effectiveness'] = np.where(self.data['price'] == 0, self.data['automation_stat'], self.data['automation_stat'] / np.where(self.data['price'] == 0, 1, self.data['price']))
        # Sort the DataFrame based on automation cost effectiveness and quality_stat as tie-breaker
        df_sorted = self.data.sort_values(by=['cost_effectiveness', 'quality_stat'], ascending=[False, False])
        
        # Select services within the budget
        total_cost = 0
        selected_services = []
        tasks_selected = set()
        for _, row in df_sorted.iterrows():
            if total_cost + row['price'] <= self.budget and row['task'] not in tasks_selected:
                total_cost += row['price']
                selected_services.append(row['service'])
                tasks_selected.add(row['task'])
        
        # Ordinal rank
        df_sorted['rank'] = range(1, len(df_sorted) + 1)
        
        self.final_df = df_sorted[['rank', 'service', 'automation_stat', 'user_auto_score', 'quality_score', 'price', 'task']].rename(
            columns={'rank': 'Rank', 'service': "Service", 'automation_stat': "Hours saved", 'quality_score': 'Quality Score', 'price': 'Price per month', 'user_auto_score': 'Hours spent', 'task': 'Task'}
        )
        assert 'Service' in self.final_df.columns
        self.final_df['selected'] = [val in selected_services for val in self.final_df['Service']]

    
        return self.final_df
    
    def md_files(self):
        return [f"{service}.md" for service in self.final_df['Service']]
