import config


class ScrollableSurface:
    def __init__(self, sidebar_subsurface, pos):
        self.sidebar_subsurface = sidebar_subsurface
        self.pos = pos
        self.domain = None
        self.surface = None
        self.scroll_surface = None
        self.scroll = None
        self.scroll_pos = 0
        self.scroll_range = None
        self.scroll_step = None
        self.surface_color = None
        self.scroll_surface_color = None
        self.scroll_color = None

    def is_displayed(self):
        return True

    def get_mouse_event_surface(self):
        return None

    def adjust_scroll(self, domain):
        self.domain = domain
        # adjust scroll height
        domain_height = self.get_domain_height()
        self.scroll[-1] = int((self.scroll_surface[-1] ** 2 / max(domain_height, self.scroll_surface[-1])))
        # reset scroll y position
        self.scroll[1] = self.scroll_surface[1]
        self.scroll_pos = 0
        # adjust scroll steps
        steps = int(
            max(domain_height - self.scroll_surface[-1], 0) / (domain_height / len(self.domain))) if self.domain else 0
        self.scroll_range = [0, steps + 1]
        self.scroll_step = (self.scroll_surface[-1] - min(self.scroll[-1],
                                                          self.scroll_surface[-1])) / steps if steps else 0

    def draw_domain(self):
        # draw scrollbar
        self.sidebar_subsurface.fill(self.surface_color, self.surface)
        self.sidebar_subsurface.fill(self.scroll_surface_color, self.scroll_surface)
        self.sidebar_subsurface.fill(self.scroll_color, self.scroll)

    def get_domain_height(self):
        return 0


class VarsScrollableSurface(ScrollableSurface):
    def __init__(self, sidebar_subsurface, pos):
        super().__init__(sidebar_subsurface, pos)
        self.surface = [0, 0, config.SIDE_WIDTH, config.HEIGHT]
        self.scroll_surface = [config.DOMAIN_WIDTH + 2 * config.PADDING, config.PADDING,
                               config.SIDE_WIDTH - config.DOMAIN_WIDTH - 3 * config.PADDING,
                               config.HEIGHT - 2 * config.PADDING]
        self.scroll = [self.scroll_surface[0] + config.PADDING, self.scroll_surface[1],
                       self.scroll_surface[2] - 2 * config.PADDING, -1]
        self.surface_color = config.BLACK
        self.scroll_surface_color = config.GRAY
        self.scroll_color = config.YELLOW
        self.children = []

    def set_children(self, children):
        self.children = children

    def draw_domain(self):
        super().draw_domain()
        for child in self.children[self.scroll_pos: self.scroll_pos + config.DOMAIN_LEN + 1]:
            child.reposition()
            child.draw_domain()

    def get_mouse_event_surface(self):
        return self.scroll_surface

    def get_domain_height(self):
        return (config.SURFACE_HEIGHT + config.PADDING) * len(self.domain)


class WordsScrollableSurface(ScrollableSurface):
    def __init__(self, sidebar_subsurface, pos, var, parent):
        super().__init__(sidebar_subsurface, pos)
        self.var = var
        self.parent = parent
        self.surface = [config.PADDING, pos * config.SURFACE_HEIGHT + (pos + 1) * config.PADDING,
                        config.DOMAIN_WIDTH, config.SURFACE_HEIGHT]
        self.scroll_surface = [self.surface[0] + self.surface[2] - 2 * config.PADDING, self.surface[1],
                               2 * config.PADDING, config.SURFACE_HEIGHT]
        self.scroll = [self.scroll_surface[0] + config.HALF_PADDING // 2, self.scroll_surface[1],
                       self.scroll_surface[2] - config.HALF_PADDING, -1]
        self.surface_color = config.WHITE
        self.scroll_surface_color = config.LIGHT_GRAY
        self.scroll_color = config.YELLOW
        self.active_var = False
        self.word = None
        self.tried = []

    def reposition(self):
        scroll_dif = self.scroll[1] - self.scroll_surface[1]
        pos = self.pos - self.parent.scroll_pos
        self.scroll_surface[1] = self.surface[1] = pos * config.SURFACE_HEIGHT + (pos + 1) * config.PADDING
        self.scroll[1] = self.scroll_surface[1] + scroll_dif

    def is_displayed(self):
        return self.pos - self.parent.scroll_pos in range(self.parent.scroll_pos + config.DOMAIN_LEN + 1)

    def draw_domain(self):
        if not self.is_displayed():
            return
        super().draw_domain()
        # draw variable name
        render_text = config.VARS_LARGER_FONT.render(self.var, True,
                                                     config.RED
                                                     if self.active_var is None
                                                     else
                                                     config.DARK_GREEN
                                                     if self.active_var
                                                     else config.BLUE)
        x = self.surface[0] + config.PADDING
        y = self.surface[1] + config.PADDING
        self.sidebar_subsurface.blit(render_text, [x, y])

        # draw variable domain
        render_text = config.VARS_FONT.render(f'{len(self.domain)}', True, config.BLUE)
        self.sidebar_subsurface.blit(render_text, [x, y + config.PADDING + config.VARS_FONT.size(self.var)[1]])
        surf_range = range(self.surface[1], self.surface[1] + self.surface[3])
        for i, word in enumerate(self.domain):
            _, text_height = config.VARS_FONT.size(word)
            render_text = config.VARS_FONT.render(word, True,
                                                  config.DARK_GREEN
                                                  if word == self.word
                                                  else config.RED
                                                  if word in self.tried
                                                  else config.BLACK)
            x = self.surface[0] + config.PADDING * 13
            y = self.surface[1] + config.PADDING + (i - self.scroll_pos) * text_height
            if y + text_height // 2 in surf_range:
                self.sidebar_subsurface.blit(render_text, [x, y])

    def get_mouse_event_surface(self):
        return self.surface

    def get_domain_height(self):
        return sum([config.VARS_FONT.size(val)[1] + config.PADDING for val in self.domain])

    def set_active_word(self, word):
        self.word = word

    def set_active_var(self, flag):
        self.active_var = flag

    def set_tried_words(self, tried):
        self.tried = tried
