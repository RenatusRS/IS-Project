from copy import deepcopy


class Algorithm:
    fields = []
    solution = []
    fields_dict = {}

    def get_algorithm_steps(self, tiles, variables, words):
        self.fields = [{
            "pos": key,
            "col": int(key[:-1]) % len(tiles[0]),
            "row": int(key[:-1]) // len(tiles[0]),
            "horizontal": key[-1] == "h",
            "size": variables[key],
            "ind": ind
        } for ind, key in enumerate(variables)]

        self.detect_constraints()

        domain = {key: [word for word in words if len(word) == variables[key]] for key in variables}

        self.backtrack(0, domain, tiles)
        return self.solution

    def detect_constraints(self):
        fields_dict = {field["pos"]: field for field in self.fields}
        
        for field in self.fields:
            current_constraints = list()

            for other_field in self.fields:
                if field["horizontal"] == other_field["horizontal"]:
                    continue
                
                if field["horizontal"]:
                    if other_field["row"] <= field["row"] <= other_field["row"] + other_field["size"] - 1 and field["col"] <= other_field["col"] <= field["col"] + field["size"] - 1:
                        current_constraints.append({
                            "field": fields_dict[other_field["pos"]],
                            "my_offset": abs(other_field["col"] - field["col"]),
                            "his_offset": abs(other_field["row"] - field["row"])
                        })
                else:
                    if other_field["col"] <= field["col"] <= other_field["col"] + other_field["size"] - 1 and field["row"] <= other_field["row"] <= field["row"] + field["size"] - 1:
                        current_constraints.append({
                            "field": fields_dict[other_field["pos"]],
                            "his_offset": abs(other_field["col"] - field["col"]),
                            "my_offset": abs(other_field["row"] - field["row"])
                        })
                                   
            field["constraints"] = current_constraints

    def add_solution(self, field, ind, domain):
        solution = [field["pos"], ind, domain]

        self.solution.append(solution)


class Backtracking(Algorithm):
    def backtrack(self, pos, domain, matrix = None):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]
        for ind, word in enumerate(domain[field["pos"]]):
            if not self.fits(field, word, matrix):
                continue

            self.add_solution(field, ind, domain)

            new_matrix = deepcopy(matrix)
            self.fill(field, word, new_matrix)

            if self.backtrack(pos + 1, domain, new_matrix):
                return True

        self.add_solution(field, None, domain)
        return False
        
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


class ForwardChecking(Algorithm):
    def backtrack(self, pos, domain, matrix = None):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]
        for ind, word in enumerate(domain[field["pos"]]):
            self.add_solution(field, ind, domain)
  
            new_domain = deepcopy(domain)

            if self.reduce_domains(field, new_domain, ind, word) and self.backtrack(pos + 1, new_domain):
                return True

        self.add_solution(field, None, domain)
        return False
    
    def forward_check(self, field, domain, my_word):
        for constraint in field["constraints"]:
            other_field = constraint["field"]
            
            if other_field["ind"] < field["ind"]:
                continue
            
            my_offset, his_offset = constraint["my_offset"], constraint["his_offset"]

            domain[other_field["pos"]] = [his_word for his_word in domain[other_field["pos"]] if his_word[his_offset] == my_word[my_offset]]

            if not domain[other_field["pos"]]:
                return False

        return True
        
    def reduce_domains(self, field, domain, passed, word):
        return self.forward_check(field, domain, word)


class ArcConsistency(ForwardChecking):
    def arc_consistency(self, domain, passed):
        changed = True
        while changed:
            changed = False
            
            for ind, field in enumerate(self.fields):
                if ind <= passed:
                    continue
                
                curr_len = len(domain[field["pos"]])
                
                for constraint in field["constraints"]:
                    other_field = constraint["field"]
                    
                    if other_field["ind"] < passed:
                        continue
                    
                    my_offset, his_offset = constraint["my_offset"], constraint["his_offset"]
                    
                    domain[field["pos"]] = [word for word in domain[field["pos"]] if any([word[my_offset] == other_word[his_offset] for other_word in domain[other_field["pos"]]])]
                    
                    if not domain[field["pos"]]:
                        return False
                
                if len(domain[field["pos"]]) != curr_len:
                    changed = True
        
        return True
                    
                        
    def reduce_domains(self, field, domain, passed, word):
        return self.forward_check(field, domain, word) and self.arc_consistency(domain, passed)
            