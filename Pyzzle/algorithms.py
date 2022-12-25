from copy import deepcopy


class Algorithm:
    fields = []
    solution = []
    fieldsDict = {}

    def get_algorithm_steps(self, tiles, variables, words):
        self.fields = [{
            "pos": key,
            "col": int(key[:-1]) % len(tiles[0]),
            "row": int(key[:-1]) // len(tiles[0]),
            "horizontal": key[-1] == "h",
            "size": variables[key],
            "ind": ind
        } for ind, key in enumerate(variables)]

        self.set_overlap()
        
        for f in self.fields:
            print(f["pos"], f["constraints"])
        
        self.fieldsDict = {field["pos"]: field for field in self.fields}

        domain = {key: [word for word in words if len(word) == variables[key]] for key in variables}

        self.backtrack(0, tiles, domain)
        return self.solution

    def set_overlap(self):
        for field in self.fields:
            current_constraints = list()

            for other_field in self.fields:
                if field["horizontal"] == other_field["horizontal"]:
                    continue
                
                if field["horizontal"]:
                    if other_field["row"] <= field["row"] <= other_field["row"] + other_field["size"] - 1 and field["col"] <= other_field["col"] <= field["col"] + field["size"] - 1:
                        current_constraints.append({
                            "field": other_field["pos"],
                            "my_offset": abs(other_field["col"] - field["col"]),
                            "his_offset": abs(other_field["row"] - field["row"])
                        })
                else:
                    if other_field["col"] <= field["col"] <= other_field["col"] + other_field["size"] - 1 and field["row"] <= other_field["row"] <= field["row"] + field["size"] - 1:
                        current_constraints.append({
                            "field": other_field["pos"],
                            "his_offset": abs(other_field["col"] - field["col"]),
                            "my_offset": abs(other_field["row"] - field["row"])
                        })
                        
                        
            field["constraints"] = current_constraints


    def fits(self, field, word, matrix):
        row, col = field["row"], field["col"]

        for char in word:
            if (matrix[row][col] != False and matrix[row][col] != char):
                return False

            if field["horizontal"]:
                col += 1
            else:
                row += 1

        return True

    def fill(self, field, word, matrix):
        row, col = field["row"], field["col"]

        for char in word:
            matrix[row][col] = char

            if field["horizontal"]:
                col += 1
            else:
                row += 1

    def add_solution(self, field, ind, domain):
        solution = [field["pos"], ind, domain]

        self.solution.append(solution)


class Backtracking(Algorithm):
    def backtrack(self, pos, matrix, domain):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]

        for ind, word in enumerate(domain[field["pos"]]):
            if not self.fits(field, word, matrix):  # Backtracking
                continue

            new_matrix = deepcopy(matrix)

            self.fill(field, word, new_matrix)
            self.add_solution(field, ind, domain)
            
            new_domain = deepcopy(domain) # Else

            if self.reduce_domains(new_matrix, new_domain, ind) and self.backtrack(pos + 1, new_matrix, new_domain):
                return True

        self.add_solution(field, None, domain)
        return False
        
    def reduce_domains(self, matrix, domain, passed):
        return True


class ForwardChecking(Backtracking):
    def forward_check(self, matrix, domain):
        for field in self.fields:
            domain[field["pos"]] = [word for word in domain[field["pos"]] if self.fits(field, word, matrix)]

            if len(domain[field["pos"]]) == 0:
                return False

        return True
        
    def reduce_domains(self, matrix, domain, passed):
        return self.forward_check(matrix, domain)


class ArcConsistency(ForwardChecking):
    def arc_consistency(self, domain, passed):
        changed = True
        while changed:
            changed = False
            
            for ind, field in enumerate(self.fields):
                if ind <= passed:
                    continue
                
                for constraint in field["constraints"]:
                    other_field = self.fieldsDict[constraint["field"]]
                    
                    if other_field["ind"] <= passed:
                        continue
                    
                    my_offset = constraint["my_offset"]
                    his_offset = constraint["his_offset"]
                    
                    curr_len = len(domain[field["pos"]])
                    domain[field["pos"]] = [word for word in domain[field["pos"]] if any([word[my_offset] == other_word[his_offset] for other_word in domain[other_field["pos"]]])]
                    
                    if len(domain[field["pos"]]) == 0:
                        return False
                        
                    if len(domain[field["pos"]]) != curr_len:
                        changed = True
        
        return True
                    
                        
    def reduce_domains(self, matrix, domain, passed):
        return self.forward_check(matrix, domain) and self.arc_consistency(domain, passed)
            