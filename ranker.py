import pandas as pd
import numpy as np
import pulp as lp

class Ranker:
    """
    Class to recommend services based on user input, review scores, and budget 
    """
    def __init__(self, budget, user_auto_scores_raw, user_quality_scores_raw, copilot):
        quality_scores = [2, 3, 9, 5, 9.5, 7, 8, 8, 9, 1, 1]
        auto_scores = [7, 5, 8, 7, 7.5, 9, 9.5, 8, 10, 10, 10]
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
        copilot_list = ["Copilot (PowerPoint)", "Copilot (Word)"]

        tasks = ["Reading texts", "PowerPoint", "PowerPoint", "Writing", "Writing", "Scheduling", "Scheduling", "Meetings", "Meetings", "Web apps (2-step)", "Web apps (multi-step)"]
        
        if None in user_auto_scores_raw:
            user_auto_scores = [0] * 11
        else:
            r1 = user_auto_scores_raw
            user_auto_scores = [r1[0], r1[1], r1[1], r1[2], r1[2], r1[3], r1[3], r1[4], r1[4], r1[5], r1[6]]
            user_auto_scores = pd.to_numeric(user_auto_scores)
        if None in user_quality_scores_raw:
            user_quality_scores = [0] * 11
        else:
            r2 = user_quality_scores_raw
            user_quality_scores = [r2[0], r2[1], r2[1], r2[2], r2[2], r2[3], r2[3], r2[4], r2[4], r2[5], r2[6]]
            user_quality_scores = pd.to_numeric(user_quality_scores)


        assert len(services) == len(user_auto_scores), f"{len(user_auto_scores)}!={len(services)}"
        assert len(services) == len(user_quality_scores), f"{len(user_quality_scores)}!={len(services)}" 
        prices = [0, 0, 12, 0, 12, 0, 19, 0, 8, 0, 20]
        self.budget = budget
        assert self.budget is not None, "Budget is missing"
        self.data = pd.DataFrame({"service": services, "user_auto_score": user_auto_scores, "user_quality_score": user_quality_scores, "auto_score": auto_scores, "quality_score": quality_scores, "price": prices, "task": tasks})

        if not copilot:
            self.data = self.data[~self.data['service'].isin(copilot_list)]
    
    def rank(self):
        # if not all(score == 0 for score in self.data['user_auto_score'].values):
        #     assert 0, f"Auto score: {self.data['auto_score']} user auto score: {self.data['user_auto_score']}"
        self.data['automation_stat'] = self.data['auto_score'] * 0.1 * self.data['user_auto_score']
        self.data['quality_stat'] = self.data['quality_score'] * 0.1 * self.data['user_quality_score']
        self.data['cost_effectiveness'] = np.where(self.data['price'] == 0, self.data['automation_stat'], self.data['automation_stat'] / np.where(self.data['price'] == 0, 1, self.data['price']))

        # Sort the DataFrame based on automation cost effectiveness and quality_stat as tie-breaker
        df_sorted = self.data.sort_values(by=['automation_stat', 'quality_stat'], ascending=[False, False])

        # Checking for non-null values before asserting sort order
        if (self.data['user_auto_score'].isnull()).all():
            selected_services = self.data['service']
        else:
            prob = lp.LpProblem("Maximize_Automation_Stat", lp.LpMaximize)

            # Create a dictionary of pulp variables with keys from the DataFrame index
            selection_vars = lp.LpVariable.dicts("Select", df_sorted.index, 0, 1, lp.LpBinary)

            # Objective Function: Maximize the sum of automation_stat for selected services
            prob += lp.lpSum([selection_vars[i] * df_sorted.loc[i, 'automation_stat'] for i in df_sorted.index])

            # Budget Constraint: The total price of selected services should not exceed the budget
            prob += lp.lpSum([selection_vars[i] * df_sorted.loc[i, 'price'] for i in df_sorted.index]) <= self.budget

            # Each task can only have one service selected
            for task in df_sorted['task'].unique():
                prob += lp.lpSum(selection_vars[i] for i in df_sorted[df_sorted['task'] == task].index) <= 1

            # Solve the problem
            prob.solve()

            # Output the selected services
            selected_services = df_sorted.loc[[i for i in df_sorted.index if selection_vars[i].varValue == 1]]['service'].values

        # if not (self.data['user_auto_score'].isnull()).all():
        #     assert (df_sorted['cost_effectiveness'].reset_index(drop=True) == df_sorted['cost_effectiveness'].sort_values(ascending=False).reset_index(drop=True)).all(), "Services are not ranked in order of saved hours"
        
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
