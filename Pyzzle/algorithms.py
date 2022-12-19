from copy import deepcopy


class Algorithm:
    fields = []
    solution = []

    def get_algorithm_steps(self, tiles, variables, words):
        pass

    def initalize(self, tiles, variables, words):
        self.fields = [{
            "pos": key,
            "col": int(key[:-1]) % len(tiles[0]),
            "row": int(key[:-1]) // len(tiles[0]),
            "horizontal": key[-1] == "h",
        } for key in variables]

        return {key: [word for word in words if len(word) == variables[key]] for key in variables}


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

        print(solution)
        self.solution.append(solution)


class ExampleAlgorithm(Algorithm):

    def get_algorithm_steps(self, tiles, variables, words):
        for tile in tiles:
            print(tile)

        print(variables)

        for word in words:
            print(word)

        moves_list = [['0h', 0], ['0v', 2], ['1v', 1], ['2h', 1], ['4h', None],
                      ['2h', None], ['1v', None], [
                          '0v', 3], ['1v', 1], ['2h', 1],
                      ['4h', 4], ['5v', 5]]

        domains = {var: ["test"] for var in variables}
        solution = []

        for move in moves_list:
            solution.append([move[0], move[1], domains])

        for var in solution:
            print(var)

        return solution


class Backtracking(Algorithm):
    def get_algorithm_steps(self, tiles, variables, words):
        domain = self.initalize(tiles, variables, words)

        self.backtrack(0, tiles, domain)
        return self.solution

    def backtrack(self, pos, matrix, domain):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]

        for ind, word in enumerate(domain[field["pos"]]):
            if not self.fits(field, word, matrix):
                continue

            new_matrix = deepcopy(matrix)

            self.fill(field, word, new_matrix)
            self.add_solution(field, ind, domain)

            if self.backtrack(pos + 1, new_matrix, domain):
                return True

        self.add_solution(field, None, domain)
        return False


class ForwardChecking(Algorithm):
    def get_algorithm_steps(self, tiles, variables, words):
        domain = self.initalize(tiles, variables, words)

        self.backtrack(0, tiles, domain)
        return self.solution

    def backtrack(self, pos, matrix, domain):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]

        for ind, word in enumerate(domain[field["pos"]]):
            new_matrix = deepcopy(matrix)

            self.fill(field, word, new_matrix)
            self.add_solution(field, ind, domain)

            new_domain = deepcopy(domain)

            if self.check_domains(new_matrix, new_domain) and self.backtrack(pos + 1, new_matrix, new_domain):
                return True

        self.add_solution(field, None, domain)

        return False

    def check_domains(self, matrix, domain):
        for field in self.fields:
            domain[field["pos"]] = [word for word in domain[field["pos"]] if self.fits(field, word, matrix)]

            if len(domain[field["pos"]]) == 0:
                return False

        return True


class ArcConsistency(ForwardChecking):
    def get_algorithm_steps(self, tiles, variables, words):
        domain = self.initalize(tiles, variables, words)

        self.backtrack(0, tiles, domain)
        return self.solution

    def backtrack(self, pos, matrix, domain):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]

        for ind, word in enumerate(domain[field["pos"]]):
            new_matrix = deepcopy(matrix)

            self.fill(field, word, new_matrix)
            self.add_solution(field, ind, domain)

            new_domain = deepcopy(domain)

            if self.check_domains(new_matrix, new_domain) and self.backtrack(pos + 1, new_matrix, new_domain):
                return True

        self.add_solution(field, None, domain)

        return False
