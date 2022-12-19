import os
import sys
import threading
import time
import traceback
from copy import deepcopy
from queue import Queue

import pygame

import config
from scrollable import VarsScrollableSurface, WordsScrollableSurface
from util import TimedFunction, Timeout


class EndGame(Exception):
    pass


class Game:
    @staticmethod
    def load_schema(schema_file):
        try:
            tiles = []
            with open(schema_file, 'r') as f:
                while True:
                    line = f.readline().strip()
                    if not len(line):
                        break
                    tiles.append([True if int(val) == 1 else False for val in line.split(',')])
                return tiles
        except Exception as e:
            raise e

    @staticmethod
    def load_words(words_file):
        try:
            words = []
            with open(words_file, 'r') as f:
                while True:
                    line = f.readline().strip()
                    if not len(line):
                        break
                    words.append(line)
                return words
        except Exception as e:
            raise e

    @staticmethod
    def get_variables(tiles):
        try:
            variables = {}
            for i in range(len(tiles)):
                for j in range(len(tiles[i])):
                    if tiles[i][j]:
                        continue
                    if not j or tiles[i][j - 1]:
                        try:
                            pos = tiles[i][j:].index(True)
                        except ValueError:
                            pos = len(tiles[i]) - j
                        variables[f'{i * len(tiles[i]) + j}h'] = pos
                    if not i or tiles[i - 1][j]:
                        column = [row[j] for row in tiles]
                        try:
                            pos = column[i:].index(True)
                        except ValueError:
                            pos = len(column) - i
                        variables[f'{i * len(tiles[i]) + j}v'] = pos
            return variables
        except Exception as e:
            raise e

    def __init__(self):
        pygame.display.set_caption('Pyzzle')
        pygame.font.init()
        config.INFO_FONT = pygame.font.Font(os.path.join(config.FONT_FOLDER, 'info_font.ttf'), 22)
        config.LETTER_FONT = pygame.font.Font(os.path.join(config.FONT_FOLDER, 'info_font.ttf'), 35)
        config.VARS_FONT = pygame.font.Font(os.path.join(config.FONT_FOLDER, 'info_font.ttf'), 13)
        config.VARS_LARGER_FONT = pygame.font.Font(os.path.join(config.FONT_FOLDER, 'info_font.ttf'), 17)
        self.screen = pygame.display.set_mode((config.WIDTH + config.SIDE_WIDTH, config.HEIGHT))
        self.info_subsurface = self.screen.subsurface((0, 0, config.WIDTH, config.SUBSURFACE_HEIGHT))
        self.sidebar_subsurface = self.screen.subsurface((config.WIDTH, 0, config.SIDE_WIDTH, config.HEIGHT))
        self.tiles = Game.load_schema(sys.argv[1] if len(sys.argv) > 1 else
                                      os.path.join(config.SCHEMA_FOLDER, 'schema0.txt'))
        self.words = Game.load_words(sys.argv[2] if len(sys.argv) > 2 else
                                     os.path.join(config.WORDS_FOLDER, 'words0.txt'))
        self.variables = Game.get_variables(self.tiles)
        self.offset_x = (config.WIDTH -
                         (len(self.tiles[0]) * config.TILE_SIZE + (len(self.tiles[0]) - 1) * config.HALF_PADDING)) // 2
        self.offset_y = (config.HEIGHT -
                         (len(self.tiles) * config.TILE_SIZE + (len(self.tiles) - 1) * config.HALF_PADDING) +
                         self.info_subsurface.get_rect()[-1] + config.PADDING) // 2
        if self.offset_x < 0 or self.offset_y - self.info_subsurface.get_rect()[-1] - config.PADDING < 0:
            raise Exception('Inadequate schema dimensions!')
        self.graphics_domains = {config.SCROLL_KEY: VarsScrollableSurface(self.sidebar_subsurface, None)}
        scroll_children = []
        for i, var in enumerate(self.variables):
            self.graphics_domains[var] = WordsScrollableSurface(self.sidebar_subsurface, i, var,
                                                                self.graphics_domains[config.SCROLL_KEY])
            scroll_children.append(self.graphics_domains[var])
        self.graphics_domains[config.SCROLL_KEY].set_children(scroll_children)

        module = __import__(config.ALGORITHMS)
        class_ = getattr(module, sys.argv[3] if len(sys.argv) > 3 else 'ExampleAlgorithm')
        self.agent = class_()
        self.max_elapsed_time = float(sys.argv[4]) if len(sys.argv) > 4 else None
        self.elapsed_time = 0.
        self.time_out = False
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.stepping = False
        self.direction = 1
        self.step = 0
        self.moves = []
        self.solution = None

    def check_solution(self):
        try:
            def get_var_coordinates(variable, var_len):
                _i, _j = int(variable[:-1]) // len(self.tiles[0]), int(variable[:-1]) % len(self.tiles[0])
                return zip(range(_i, var_len + _i), [_j] * var_len) \
                    if variable[-1] != 'h' \
                    else zip([_i] * var_len, range(_j, var_len + _j))

            def add_letters(variable, word, matrix):
                letters_new = []
                letters_old = []
                for k, (i, j) in enumerate(get_var_coordinates(variable, self.variables[variable])):
                    if matrix[i][j] is None or (matrix[i][j] != '_' and matrix[i][j] != word[k]):
                        msg = f'ERROR: Position ({i}, {j}) '
                        msg += f'already contains letter \'{matrix[i][j]}\', but \'{word[k]}\' was tried.' \
                            if matrix[i][j] else 'cannot be assigned (black tile).'
                        print(msg)
                        raise EndGame()
                    if matrix[i][j] != word[k]:
                        matrix[i][j] = word[k]
                        letters_new.append([i, j, word[k]])
                    else:
                        letters_old.append([i, j, word[k]])
                return letters_new, letters_old

            def remove_letters(letters, matrix):
                for i, j, _ in letters:
                    matrix[i][j] = '_'

            variables = []
            letters_pair = {}
            letter_matrix = [[None if tile else '_' for tile in row] for row in self.tiles]
            tried_values = {var: [] for var in self.variables}

            orig_domains = {var: [word for word in self.words] for var in self.variables}
            self.solution.insert(0, [None, None, orig_domains])
            self.moves.append([*self.solution[0], [[], []], tried_values])
            for var, val_ind, domains in self.solution[1:]:
                tried_values = deepcopy(tried_values)
                if val_ind is not None:
                    value = domains[var][val_ind]
                    if len(value) != self.variables[var]:
                        return False, f'Value \'{value}\' cannot fit ' \
                                      f'variable \'{var}\' of length {self.variables[var]}.'
                    if value not in self.words:
                        return False, f'Value \'{value}\' does not belong to initial domain: {self.words}.'
                    if var not in variables:  # forward
                        variables.append(var)
                    elif var in letters_pair:  # change value, add empty back step
                        remove_letters(letters_pair[var][0], letter_matrix)
                        self.moves.append([var, -1, domains, letters_pair[var], tried_values])
                        tried_values = deepcopy(tried_values)
                        del letters_pair[var]
                    letters_pair[var] = add_letters(var, value, letter_matrix)
                    self.moves.append([var, val_ind, domains, letters_pair[var], tried_values])
                    if value in tried_values[var]:
                        return False, f'Value \'{value}\' of variable \'{var}\' already tried.'
                    tried_values[var].append(value)
                else:
                    added_move = False
                    if variables and var == variables[-1]:  # backward
                        var = variables.pop(-1)
                        if var in letters_pair:
                            remove_letters(letters_pair[var][0], letter_matrix)
                            self.moves.append([var, val_ind, domains, letters_pair[var], tried_values])
                            added_move = True
                            tried_values[var].clear()
                            del letters_pair[var]
                    if not added_move:
                        self.moves.append([var, val_ind, domains, [[], []], tried_values])
                        tried_values[var].clear()
            flag = len(variables) == len(self.variables)
            return flag, f'Ok.' if flag else 'Backtrack was not executed properly.'
        except (Exception,):
            traceback.print_exc()
            return False, 'An exception occurred.'

    def run(self):

        def apply(letters, color):
            self.draw_tiles_letters(letters, color)

        def revert(new_letters, old_letters, color):
            for i, j, _ in new_letters:
                self.draw_initial_tile(i, j)
            self.draw_tiles_letters(old_letters, color)

        def draw_move(move_ind, latest_flag, apply_color, revert_color):
            if move_ind:
                var, val_ind, domains, letters, _ = self.moves[move_ind]

                value_flag = val_ind not in [None, -1]
                direction_flag = self.direction == 1 and value_flag or self.direction == -1 and not value_flag
                all_letters = ''.join([elem[-1] for elem in sorted(letters[0] + letters[1])])
                bc_flag = latest_flag and value_flag or not latest_flag and all_letters and direction_flag
                word = all_letters if bc_flag else None
                self.graphics_domains[var].set_tried_words(self.moves[self.step][-1][var])
                self.graphics_domains[var].set_active_word(word)
                self.graphics_domains[var].set_active_var(True if bc_flag else None if latest_flag else False)

                apply_flag = value_flag if latest_flag else direction_flag
                if apply_flag:
                    apply(letters[0] + letters[1], apply_color)
                else:
                    revert(letters[0], letters[1], revert_color)

        def make_step():
            self.step += self.direction
            before_latest_change, latest_change = self.step - self.direction, self.step
            draw_move(before_latest_change, False, config.BLACK, config.BLACK)
            draw_move(latest_change, True, config.GREEN, config.BLACK)
            for var in self.variables:
                self.graphics_domains[var].adjust_scroll(self.moves[self.step][2][var])
                self.graphics_domains[var].draw_domain()

        self.draw_initial()
        while self.running:
            try:
                try:
                    if self.solution is None and not self.time_out:
                        tf_queue = Queue(1)
                        tf = TimedFunction(threading.current_thread().ident, tf_queue,
                                           self.max_elapsed_time, self.agent.get_algorithm_steps,
                                           deepcopy(self.tiles), self.variables.copy(), self.words.copy())
                        tf.daemon = True
                        tf.start()
                        start_time = time.time()
                        sleep_time = 0.001
                        while tf_queue.empty():
                            time.sleep(sleep_time)
                            self.elapsed_time = time.time() - start_time
                            self.draw_info_text()
                            self.events()
                        self.solution, elapsed = tf_queue.get(block=False)
                        if self.solution is None:
                            raise elapsed
                        status = self.check_solution()
                        if not status[0]:
                            self.moves = []
                            print(f'ERROR: Algorithm steps check failed! Reason - {status[1]}')
                            raise EndGame()
                        self.draw_info_text()
                        print(f'INFO: Algorithm elapsed time is {elapsed:.3f} seconds.')
                except Timeout:
                    print(f'ERROR: Algorithm took more than {self.max_elapsed_time} seconds!')
                    self.time_out = True
                    raise EndGame()

                if self.stepping:
                    self.stepping = False
                    make_step()
                    self.draw_info_text()
                self.clock.tick(config.FRAME_RATE)
                self.events()
            except EndGame:
                self.game_over = True
                if self.running and self.moves:
                    self.step = 0
                    self.direction = 1
                    for _ in range(len(self.moves) - 1):
                        make_step()
                self.draw_info_text()
            except Exception as e:
                raise e

    def draw_initial(self):
        self.screen.fill(config.GRAY, rect=(0, 0, config.WIDTH, config.HEIGHT))
        self.screen.fill(config.BLACK, rect=(config.WIDTH, 0, config.SIDE_WIDTH, config.HEIGHT))
        self.screen.fill(config.BLACK, rect=[config.LINE_PADDING, self.info_subsurface.get_rect()[-1],
                                             config.WIDTH - 2 * config.LINE_PADDING, config.PADDING])
        for i in range(len(self.tiles)):
            for j in range(len(self.tiles[i])):
                self.draw_initial_tile(i, j)
        self.graphics_domains[config.SCROLL_KEY].adjust_scroll(self.variables)
        for var in self.variables:
            self.graphics_domains[var].adjust_scroll(self.words)
        self.graphics_domains[config.SCROLL_KEY].draw_domain()
        self.draw_info_text()

    def draw_initial_tile(self, i, j):
        y = self.offset_y + i * (config.TILE_SIZE + config.HALF_PADDING)
        x = self.offset_x + j * (config.TILE_SIZE + config.HALF_PADDING)
        self.screen.fill(config.BLACK if self.tiles[i][j] else config.WHITE,
                         rect=(x, y, config.TILE_SIZE, config.TILE_SIZE))
        num = i * len(self.tiles[i]) + j
        if (key := f'{num}h') in self.variables:
            text = config.VARS_FONT.render(key, True, config.BLACK)
            _, text_height = config.VARS_FONT.size(key)
            self.screen.blit(text, (x + config.HALF_PADDING, y + config.TILE_SIZE - text_height))
        if (key := f'{num}v') in self.variables:
            text = config.VARS_FONT.render(key, True, config.BLACK)
            self.screen.blit(text, (x + config.HALF_PADDING, y + config.HALF_PADDING))

    def draw_tiles_letters(self, letters, color):
        for i, j, l in letters:
            self.draw_initial_tile(i, j)
            letter_width, letter_height = config.LETTER_FONT.size(l)
            letter_surface = config.LETTER_FONT.render(f'{l}', True, color)
            x = self.offset_x + j * (config.TILE_SIZE + config.HALF_PADDING) + config.TILE_SIZE // 2 \
                - letter_width // 2
            y = self.offset_y + i * (config.TILE_SIZE + config.HALF_PADDING) + config.TILE_SIZE // 2 \
                - letter_height // 2
            self.screen.blit(letter_surface, (x, y))

    def draw_info_text(self):
        self.info_subsurface.fill(config.GRAY)
        offset_y = self.info_subsurface.get_rect()[-1] // 2
        if self.time_out:
            text = 'TIMED OUT'
        elif self.solution is None:
            text = f'CALCULATING {"." * (int(self.elapsed_time * 4) % 4)}'
        elif self.game_over:
            text = 'GAME OVER'
        else:
            var, val_ind, domains, _, _ = self.moves[self.step]
            if self.step:
                text = f'{"[Backtrack] " if val_ind is None else "" if val_ind != -1 else "[Value change] "}'
                text += f'Var: {var}'
                text += f' | val: {domains[var][val_ind]}' if val_ind not in [None, -1] else ''
                render_text = config.INFO_FONT.render(text, True, config.WHITE)
                text_width, text_height = config.INFO_FONT.size(text)
                self.info_subsurface.blit(render_text, (config.WIDTH // 2 - text_width // 2, offset_y + config.PADDING))
                offset_y -= text_height // 2
            text = f'STEP {self.step}/{len(self.moves) - 1}'

        render_text = config.INFO_FONT.render(text, True, config.WHITE)
        text_width, text_height = config.INFO_FONT.size(text)
        if not self.time_out and self.solution is None:  # calculating
            render_text.set_alpha([159, 191, 223, 255][text.count('.')])
            if self.max_elapsed_time:
                x, y, w, h, m = config.TIMER_MARGINS
                self.info_subsurface.fill(config.BLACK, rect=(x, y, w, h))
                perc_left = max(int((1 - self.elapsed_time / self.max_elapsed_time) * 100), 0)
                self.info_subsurface.fill(config.R_to_G[perc_left],
                                          rect=(x + m, y + m, w * perc_left * 0.01 - 2 * m, h - 2 * m))
                time_left = max(self.max_elapsed_time - self.elapsed_time, 0)
                time_text = f'{time_left:.3f}s'
                render_time_text = config.VARS_FONT.render(time_text, True, config.WHITE)
                time_text_width, time_text_height = config.VARS_FONT.size(time_text)
                self.info_subsurface.blit(render_time_text,
                                          (x + w // 2 + m // 2 - time_text_width // 2,
                                           y + h // 2 - m // 2 - time_text_height // 2))
        self.info_subsurface.blit(render_text, (config.WIDTH // 2 - text_width // 2, offset_y - text_height // 2))
        pygame.display.flip()

    def events(self):
        # catch all events here
        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for gd in self.graphics_domains.values():
                    if not gd.is_displayed():
                        continue
                    ev_surface = gd.get_mouse_event_surface()
                    direction = -event.y
                    if mouse_x in range(config.WIDTH + ev_surface[0], config.WIDTH + ev_surface[0] + ev_surface[2]) \
                            and mouse_y in range(ev_surface[1], ev_surface[1] + ev_surface[3]):
                        if gd.scroll_pos + direction in range(gd.scroll_range[0], gd.scroll_range[1]):
                            gd.scroll_pos += direction
                            gd.scroll[1] += direction * gd.scroll_step
                            gd.scroll[1] = min(max(gd.scroll[1], gd.scroll_surface[1]),
                                               gd.scroll_surface[1] + gd.scroll_surface[3] - gd.scroll[-1])
                            gd.draw_domain()
                            pygame.display.flip()
                            break
                        elif direction == -1:  # wheel up
                            gd.scroll[1] = gd.scroll_surface[1]
                            gd.draw_domain()
                            pygame.display.flip()
                        elif direction == 1:  # wheel down
                            gd.scroll[1] = gd.scroll_surface[1] + gd.scroll_surface[3] - gd.scroll[-1]
                            gd.draw_domain()
                            pygame.display.flip()
            if event.type == pygame.QUIT or event.type == pygame.WINDOWCLOSE or \
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                raise EndGame()
            if self.game_over or self.solution is None:
                pass
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT and self.step < len(self.moves) - 1:
                self.stepping = True
                self.direction = 1
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT and self.step > 0:
                self.stepping = True
                self.direction = -1
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                raise EndGame()
