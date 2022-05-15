import math
import sys
import copy
import random
import time

SIZE = 0
START_BOARD = []
IS_FIXED = []
INEQUALITY = {}
START_MUTATION_RATE = 0.01
MUTATION_RATE = START_MUTATION_RATE
REFRESH_MUTATION_RATE = 0.2
TARGET_SCORE = 0


def parse_input():
    global SIZE, IS_FIXED, START_BOARD, TARGET_SCORE

    with open(sys.argv[1], 'r') as file:
        # create board and fixed board
        SIZE = int(file.readline())
        for _ in range(SIZE):
            START_BOARD.append([0 for _ in range(SIZE)])
            IS_FIXED.append([False for _ in range(SIZE)])

        # insert fixed digits
        num_of_fixed = int(file.readline())
        for _ in range(num_of_fixed):
            d = file.readline().split(' ')
            i = int(d[0]) - 1
            j = int(d[1]) - 1
            n = int(d[2])
            START_BOARD[i][j] = n
            IS_FIXED[i][j] = True

        # insert inequalities
        ineq = int(file.readline())
        for _ in range(ineq):
            l = [int(i) - 1 for i in file.readline().split(' ')]
            if (l[0], l[1]) not in INEQUALITY: INEQUALITY[(l[0], l[1])] = []
            INEQUALITY[(l[0], l[1])].append((l[2], l[3]))

        file.close()
        TARGET_SCORE = SIZE*SIZE + ineq
        print(f'target: {TARGET_SCORE}')


class Solution:
    def __init__(self, board=None):
        self.fitness = None
        self.board = []
        if board != None:
            self.board = board
        else:
            for row in START_BOARD:
                r = []
                nums = list(range(1, SIZE + 1))
                for n in row:
                    if n != 0: nums.remove(n)
                random.shuffle(nums)
                for i in range(SIZE):
                    if row[i] != 0:
                        r.append(row[i])
                    else:
                        r.append(nums.pop())
                self.board.append(r)


    def __copy__(self):
        b = []
        for line in self.board:
            b.append(line.copy())
        f = self.fitness
        s = Solution(b)
        s.fitness = f
        return s


    def __eq__(self, other):
        if other == None: return False
        if other.fitness == self.fitness:
            for i in range(len(self.board)):
                if self.board[i] != other.board[i]:
                    return False
            return True
        return False


    def print_board(self):
        for line in self.board:
            print(line)


    def mutate(self):
        line_idx = random.randint(0, SIZE-1)
        while True:
            v1 = random.randint(0, SIZE-1)
            v2 = random.randint(0, SIZE-1)
            if IS_FIXED[line_idx][v1] or IS_FIXED[line_idx][v2]: continue
            line = self.board[line_idx]
            temp = line[v1]
            line[v1] = line[v2]
            line[v2] = temp
            self.fitness = None
            break


    def calc_fitness(self):
        if self.fitness != None: return self.fitness

        def check_column(j):
            elements_in_column = []
            for i in range(SIZE):
                elements_in_column.append(self.board[i][j])
            unique = set(elements_in_column)
            return len(unique)

        def check_ineq(i, j):
            if (i, j) not in INEQUALITY: return 0
            count = 0
            for t in INEQUALITY[(i, j)]:
                if self.board[i][j] > self.board[t[0]][t[1]]:
                    count += 1
            return count

        total = 0
        for i in range(SIZE):
            for j in range(SIZE):
                if (i, j) in INEQUALITY:
                    total += check_ineq(i, j)

        for j in range(SIZE):
            total += check_column(j)

        # print(columns)
        self.fitness = total

        # TEST FITNESS FUNCTION CORRECTION
        # print(self.fitness)
        # self.print_board()
        # exit(1)

        return self.fitness


class Futoshiki:
    def __init__(self, population, replication_rate, random_rate, gen_limit, restart_threshold):
        self.n = population
        self.replication_percent = replication_rate
        self.random_rate = random_rate
        self.trials = int(gen_limit / restart_threshold)
        self.restart_threshold = restart_threshold

        self.population = [Solution() for _ in range(population)]
        self.fitness_sum = sum([sol.calc_fitness() for sol in self.population])
        self.prob_array = [sol.calc_fitness() / self.fitness_sum for sol in self.population]


    def worst_fitness(self):
        return min([sol.calc_fitness() for sol in self.population])


    def best_fitness(self):
        return max([sol.calc_fitness() for sol in self.population])


    def average_Score(self):
        return sum([sol.calc_fitness() for sol in self.population]) / len(self.population)


    def update_population(self, new_population):
        self.population = new_population
        self.fitness_sum = sum([sol.calc_fitness() for sol in self.population])
        self.prob_array = [sol.calc_fitness() / self.fitness_sum for sol in self.population]


    def replicate_elite(self):
        solution_to_score = {}
        for i, sol in enumerate(self.population):
            solution_to_score[i] = sol.calc_fitness()
        sorted_by_scores = sorted(solution_to_score.items(), key=lambda item: item[1])
        num = int(self.replication_percent * self.n)
        best_pairs = sorted_by_scores[self.n - num:]
        best = []
        for pair in best_pairs:
            best.append(copy.copy(self.population[pair[0]]))
        return best


    def sample_solution_and_remove(self):
        val = random.choices(self.population, self.prob_array)[0]
        # self.population.remove(val)
        # self.update_population(self.population)
        return val


    def crossover(self, parent1, parent2):
        rows = random.randint(1, SIZE - 1)
        board = parent1.board[:rows] + parent2.board[rows:]
        return Solution(board)

    # def check_how_many_equal_best(self, best: Solution):
    #     count = 0
    #     for sol in self.population:
    #         if sol == best:
    #             count += 1
    #     return count - 1


    def mutate(self, sol):
        sol.mutate()


    def get_best(self, pop):
        sol = pop[0]
        for sol2 in pop:
            if sol2.calc_fitness() > sol.calc_fitness():
                sol = sol2
        return sol


    def generate_population(self):
        self.update_population([Solution() for _ in range(self.n)])


    def run_single(self):
        global MUTATION_RATE
        best = Solution()
        gen = 0

        while True:
            if gen >= self.restart_threshold: return best
            current_best = self.get_best(self.population)
            if current_best.calc_fitness() == TARGET_SCORE:
                return current_best
            if current_best.calc_fitness() > best.calc_fitness():
                best = current_best
                print(f'at gen {gen} new best {best.calc_fitness()}, target {TARGET_SCORE}:')
                best.print_board()

            new_population = self.replicate_elite()

            if gen % 100 == 0:
                num_of_random = int(self.random_rate * self.n)
                for i in range(num_of_random):
                    new_population.append(Solution())

            while len(new_population) < self.n:
                parent1 = self.sample_solution_and_remove()
                parent2 = self.sample_solution_and_remove()

                child = self.crossover(parent1, parent2)

                mutationChance = random.random()
                if mutationChance < MUTATION_RATE:
                    self.mutate(child)

                new_population.append(child)

            self.update_population(new_population)
            gen += 1


    def run(self):
        num = 0
        best_solutions = []
        while num < self.trials:
            self.generate_population()
            best_in_run = self.run_single()
            if best_in_run.calc_fitness() == TARGET_SCORE:
                print(f'best in run: {best_in_run.calc_fitness()}')
                best_in_run.print_board()
                return best_in_run
            best_solutions.append(best_in_run)
            num += 1
            print(f'Done with trial {num}')
        return self.get_best(best_solutions)


parse_input()
f = Futoshiki(population=100, replication_rate=0.01, random_rate=0.01, gen_limit=50000, restart_threshold=5000)
solution = f.run()
if solution:
    print(f'Final solution:')
    solution.print_board()
else:
    print('No solution found.')

