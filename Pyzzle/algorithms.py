from copy import deepcopy


class Algorithm:
    fields = []
    solution = []

    def get_algorithm_steps(self, tiles, variables, words):
        pass

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

    def add_solution(self, field, ind):
        solution = [field["pos"], ind, {field["pos"]: [
            word for word in field["domain"]] for field in self.fields}]

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
        self.fields = [{
            "pos": key,
            "col": int(key[:-1]) % len(tiles[0]),
            "row": int(key[:-1]) // len(tiles[0]),
            "horizontal": key[-1] == "h",
            "domain": [word for word in words if len(word) == variables[key]]
        } for key in variables]

        self.backtrack(0, tiles)
        return self.solution

    def backtrack(self, pos, matrix):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]

        for ind, word in enumerate(field["domain"]):

            if self.fits(field, word, matrix):
                new_matrix = deepcopy(matrix)

                self.fill(field, word, new_matrix)
                self.add_solution(field, ind)

                if self.backtrack(pos + 1, new_matrix):
                    return True

        self.add_solution(field, None)
        return False


class ForwardChecking(Algorithm):
    def get_algorithm_steps(self, tiles, variables, words):
        self.fields = [{
            "pos": key,
            "col": int(key[:-1]) % len(tiles[0]),
            "row": int(key[:-1]) // len(tiles[0]),
            "horizontal": key[-1] == "h",
            "domain": [word for word in words if len(word) == variables[key]]
        } for key in variables]

        self.backtrack(0, tiles)
        return self.solution

    def backtrack(self, pos, matrix):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]

        for ind, word in enumerate(field["domain"]):
            new_matrix = deepcopy(matrix)
            fieldC = deepcopy(self.fields)

            self.fill(field, word, new_matrix)
            self.add_solution(field, ind)

            if self.check_domains() and self.backtrack(pos + 1, new_matrix):
                return True

            self.fields = fieldC

        self.add_solution(field, None)

        return False

    def check_domains(self):
        for field in self.fields:
            field["domain"] = [word for word in field["domain"]
                               if self.fits(word, field)]

            if len(field["domain"]) == 0:
                return False

        return True


class ArcConsistency(ForwardChecking):
    def get_algorithm_steps(self, tiles, variables, words):
        self.fields = [{
            "pos": key,
            "col": int(key[:-1]) % len(tiles[0]),
            "row": int(key[:-1]) // len(tiles[0]),
            "horizontal": key[-1] == "h",
            "size": variables[key],
            "domain": [word for word in words if len(word) == variables[key]]
        } for key in variables]

        self.spots = tiles
        self.words = words

        for field in self.fields:
            print(field)

        print("SOLUTION")

        self.backtrack(0)
        return self.solution

    def backtrack(self, pos):
        if pos == len(self.fields):
            return True

        field = self.fields[pos]
        ind = 0
        for word in field["domain"]:
            spots = deepcopy(self.spots)
            fieldC = deepcopy(self.fields)

            self.fits(word, field, True)

            self.solution.append([field["pos"], ind, {field["pos"]: [
                                 word for word in field["domain"]] for field in self.fields}])
            print([field["pos"], ind, {field["pos"]: [
                  word for word in field["domain"]] for field in self.fields}])

            if self.check_domains() and self.backtrack(pos + 1):
                return True

            self.fields = fieldC
            self.spots = spots
            ind += 1

        self.solution.append([field["pos"], None, {field["pos"]: [
                             word for word in field["domain"]] for field in self.fields}])
        print([field["pos"], None, {field["pos"]: [
              word for word in field["domain"]] for field in self.fields}])

        return False
