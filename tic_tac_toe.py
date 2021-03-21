from math import floor
import os
import pygame
from pygame.locals import *
from random import choice

# Game constants
WIN_SIZE = WIN_WIDTH, WIN_HEIGHT = 800, 600
BLACK = 0, 0, 0
WHITE = 255, 255, 255
RED = 255, 0, 0
BLUE = 0, 0, 255
GREY = 192, 192, 192

START_SCREEN = "start screen"
GAME_SCREEN = "game screen"
ADDITIONAL_OPTIONS_SCREEN = "additional options screen"
GAME_HISTORY_SCREEN = "game history screen"
PAST_GAME_SCREEN = "past game screen"

# Game functions
class NoneSound:
    """dummy class for when pygame.mixer did not init 
    and there is no sound available"""
    def play(self): pass

class NoneFont:
    """dummy class for when pygame.font did not init
    and there is font available"""
    def render(self, t=None, a=None, c=None, b=None): pass


def load_sound(file):
    """loads a sound file, prepares it for play"""
    if not pygame.mixer:
        return NoneSound()
    
    music_to_load = os.path.join('sounds', file)
    try:
        sound = pygame.mixer.Sound(music_to_load)
    except pygame.error as message:
        print('Cannot load following sound:', music_to_load)
        raise SystemExit(message)
    
    return sound

def load_font(name, size):
    """Loads a system font by name"""
    if not pygame.font:
        return NoneFont()
    font = pygame.font.SysFont(name, size)
    return font


def load_image(file, colorkey=None, size=None, alpha=None):
    """loads image into game"""
    image_to_load = os.path.join('images', file)
    try:
        image = pygame.image.load(image_to_load).convert()
    except pygame.error as message:
        print('Cannot load following image:', image_to_load)
        raise SystemExit(message)
    
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    
    if size is not None:
        image = pygame.transform.scale(image, size)

    if alpha is not None:
        image.set_alpha(alpha)
    
    return image

def rotozoom(surface: pygame.Surface, angle, scale):
    width, height = surface.get_rect().size
    new_surface = pygame.transform.scale(surface, (floor(width*scale), floor(height*scale)))
    new_surface = pygame.transform.rotate(new_surface, angle)    
    return new_surface


class TTTVisual:
    """handles the visual aspects of the game"""
    # TODO: MOVE ALL RECTS TO LAYOUTS CLASS

    def __init__(self, win: pygame.Surface, texts):
        self.win, self.win_rect = win, win.get_rect()
        self.layouts = Layouts(self.win, texts)  # object with all Rects that will be used in the game
        ### load in all game images
        self.grid = load_image("grid.png", WHITE, 
                               size=(floor(self.win_rect.width*0.5), floor((self.win_rect.height*0.8)*0.8)))
        self.x_tile_og = load_image("X_tile.png", WHITE)
        self.o_tile_og = load_image("O_tile.png", WHITE)
        self.x_line_og = load_image("X_line.png", WHITE)
        self.o_line_og = load_image("O_line.png", WHITE)
        self.more_button_og = load_image("more_button.png", WHITE)
        self.dark_background = load_image("darkbackground.png", size=self.win_rect.size, alpha=150)

        self.layouts.create_grid_layout(self.grid)
        self.create_XO_tiles()
        self.layouts.create_game_info_layout(self.x_turn_tile, self.o_turn_tile)

        self.create_more_button()
        self.create_XO_lines()

        self.texts = texts

        self.screens = {
        # Copy of these surfaces will be added when switching from one screen to the other.
        # Eg. When switching from 'game screen' to 'additional options screen', copy of 'game screen' will
        # be made and entered into self.screens['game screen']
            GAME_SCREEN: None,
            ADDITIONAL_OPTIONS_SCREEN: None,
            GAME_HISTORY_SCREEN: None
        }

    def create_XO_tiles(self):
        """Create X and O tiles that will be placed on the grid and the X and O tiles that will
        indicate whose turn it is"""
        grid_tile_size = self.layouts.grid_tile_rects[0][1].size
        # scale X and O tiles to be same size as each tile
        self.x_grid_tile = pygame.transform.scale(self.x_tile_og, grid_tile_size)
        self.o_grid_tile = pygame.transform.scale(self.o_tile_og, grid_tile_size)

        ## Tiles to indicate turn status
        self.x_turn_tile = pygame.transform.scale(self.x_tile_og, (50, 50))
        self.o_turn_tile = pygame.transform.scale(self.o_tile_og, (50, 50))

    def create_XO_lines(self):
        """Creates red and blue lines that will be used to cross across a winning grid
        red = X winner and blue = O winner"""
        # straight lines for row and column wins
        size = self.o_line_og.get_rect().width, self.layouts.grid_rect.height
        x_line = pygame.transform.scale(self.x_line_og, size)
        o_line = pygame.transform.scale(self.o_line_og, size)
        self.x_lines = (x_line, pygame.transform.rotate(x_line, 90),
                        rotozoom(x_line, -47, 1.2), rotozoom(x_line, 47, 1.2))
        self.o_lines = (o_line, pygame.transform.rotate(o_line, 90),
                        rotozoom(o_line, -47, 1.2), rotozoom(o_line, 47, 1.2))

    def create_more_button(self):
        """Scales 'more' button to proper size and gets its Rect in the layout"""
        section = pygame.Rect(floor(self.win_rect.width*(2/3)), floor(self.win_rect.height*(8/10)),
                              floor(self.win_rect.width*(1/3)), floor(self.win_rect.height*(2/10)))
        self.more_button = pygame.transform.scale(self.more_button_og, (floor(section.width*(4/10)), floor(section.height*(8/10))))
        self.more_button_rect = self.more_button.get_rect(center=section.center)

    def create_additional_options(self) -> list:
        """Places layout of additional options in a list for blitting"""
        options = []
        option_texts = [self.texts["history"], pygame.Surface((50,50)), pygame.Surface((50,50))]
        # Rect for white rectangular container surrounding the additional options
        x, y = -floor(self.win_rect.width*(1/2)), -floor(self.win_rect.height*(1/2))
        container_rect = self.win_rect.inflate(x, y)
        # splits the rectangular container into three horizontal Rects
        height = floor(container_rect.height*(1/3))
        for i in range(3):
            new_rect = container_rect.copy()
            new_rect.height = height
            if i != 0:
                new_rect.top += floor(container_rect.height*(i/3))
            else:
                pass
            options.append((option_texts[i], option_texts[i].get_rect(center=new_rect.center)))
        options.append(container_rect)
        return options
     
    def draw_start_screen(self):
        """Draws start screen of game. Just a white screen with big play button"""
        self.win.fill(WHITE)
        x, y = floor(self.win_rect.width*(7/10)), floor(self.win_rect.height*(8/10))
        self.play_button_rect = self.win_rect.inflate(-x, -y)
        pygame.draw.rect(self.win, GREY, self.play_button_rect)
        self.win.blit(self.texts["play"], self.texts["play"].get_rect(center=self.play_button_rect.center))
        pygame.display.flip()

    def draw_game_screen(self, turn, turn_count):
        """Draws the game screen on the window. Includes grid and all the other stuff."""
        self.win.fill(WHITE)
        self.win.blit(self.grid, self.layouts.grid_rect)
        
        # test ground TODO: remove this

        self.update_turn_tiles(turn)
        self.update_turn_count(turn_count, set_game_screen=True)
        self.draw_more_button()
        pygame.display.flip()

    def draw_grid(self, game_data):
        """Algorithm to draw grid with list representing grid"""
        grid, _, _ = game_data
        self.win.blit(self.grid, self.layouts.grid_rect)
        grid_to_blit = []
        for index in range(len(grid)):
            turn = grid[index]
            tile = self.layouts.grid_tile_rects[index][1]
            if turn is None:
                continue
            elif turn == 'x':
                grid_to_blit.append((self.x_grid_tile, tile))
            else:
                grid_to_blit.append((self.o_grid_tile, tile))
        self.win.blits(grid_to_blit)

    def draw_past_game_screen(self, game_data):
        """Draws a past game selected from the game history screen"""
        self.screens[GAME_HISTORY_SCREEN] = self.win.copy()

        self.win.fill(WHITE)
        self.draw_grid(game_data)
        pygame.draw.polygon(self.win, GREY, self.layouts.past_game_back_arrow)

        pygame.display.flip()

    def update_tile(self, index, turn):
        """Draws either X or O on tile when tile is clicked"""
        tile = self.layouts.grid_tile_rects[index][1]
        if turn == "x":
            self.win.blit(self.x_grid_tile, tile)
        elif turn == "o":
            self.win.blit(self.o_grid_tile, tile)
        pygame.display.update(tile)
    
    def update_turn_tiles(self, turn):
        """Changes the transparency of the two turn tiles to indicate whose turn it is"""
        self.win.fill(WHITE, self.layouts.x_turn_tile_rect)
        self.win.fill(WHITE, self.layouts.o_turn_tile_rect)
        if turn is None:
            self.x_turn_tile.set_alpha(80)
            self.o_turn_tile.set_alpha(80)
        elif turn == "x":
            self.o_turn_tile.set_alpha(80)
            self.x_turn_tile.set_alpha(255)
        else:
            self.x_turn_tile.set_alpha(80)
            self.o_turn_tile.set_alpha(255)
        
        self.win.blit(self.x_turn_tile, self.layouts.x_turn_tile_rect)
        self.win.blit(self.o_turn_tile, self.layouts.o_turn_tile_rect)
        pygame.display.update(self.layouts.x_turn_tile_rect)
        pygame.display.update(self.layouts.o_turn_tile_rect)

    def update_turn_count(self, turn_count, *, set_game_screen=False, game_over=False, tie=False):
        """Update the turn counter. If being called from set_game_screen(), it will also blit "Current turn:" on top of the
        turn counter"""
        if set_game_screen:
            self.win.blit(self.texts["currentturn"], 
                          self.texts["currentturn"].get_rect(center=self.layouts.turn_count_text_rect.center))
        elif game_over:
            self.win.fill(WHITE, self.layouts.turn_count_text_rect)
            self.win.blit(self.texts["gamewonin?turns"], 
                          self.texts["gamewonin?turns"].get_rect(center=self.layouts.turn_count_text_rect.center))
            pygame.display.update(self.layouts.turn_count_text_rect)
        elif tie:
            self.win.fill(WHITE, self.layouts.turn_count_text_rect)
            self.win.fill(WHITE, self.layouts.turn_count_rect)
            # the rect is a union of the two rects that make up the turn count section, so it centers perfectly
            self.win.blit(self.texts["tiegame"],
                          self.texts["tiegame"].get_rect(center=self.layouts.turn_count_rect.union(self.layouts.turn_count_text_rect).center))
            pygame.display.update(self.layouts.turn_count_text_rect)
            pygame.display.update(self.layouts.turn_count_rect)

        if turn_count is not None:
            turn_count_surface = self.texts["majorfont"].render(str(turn_count), True, BLACK, WHITE)
            rect = turn_count_surface.get_rect(center=self.layouts.turn_count_rect.center)
            self.win.blit(turn_count_surface, rect)
            pygame.display.update(self.layouts.turn_count_rect)

    def draw_more_button(self):
        """Adds the 'more' button to the game screen layout"""
        self.win.blit(self.more_button, self.more_button_rect)

    def draw_line(self, win_info, turn):
        """When there is a winner, draws line to cross over winning tiles. Doesn't do anything if it's a tie"""
        if win_info == "tie":
            return
        center = self.layouts.grid_tile_rects[win_info[0]][0].center
        dir = win_info[1]

        if turn == "x":
            line = self.x_lines[dir]
            self.win.blit(line, line.get_rect(center=center))
        else:
            line = self.o_lines[dir]
            self.win.blit(line, line.get_rect(center=center))

        pygame.display.update(self.layouts.grid_rect)

    def draw_additional_options_screen(self):
        """Darkens game and shows additional settings layout"""
        # Keep copy of "game screen" Surface for when we want to go back
        self.screens[GAME_SCREEN] = self.win.copy()

        # darkens the background
        self.win.blit(self.dark_background, self.win_rect)
        # create Rect for additional options square then draw it
        pygame.draw.rect(self.win, WHITE, self.layouts.additional_options_container)
        self.win.blits(self.layouts.additional_options)
        pygame.display.flip()

    def go_back_to_prev_screen(self, screen):
        """Exits the modal screen and reblits the previous surface"""
        self.win.fill(WHITE)
        self.win.blit(self.screens[screen], self.win_rect)
        pygame.display.flip()

    def draw_game_history_screen(self, game_history, index):
        """Shows screen with all previous games you have played"""
        if self.screens[ADDITIONAL_OPTIONS_SCREEN] is None:
            self.screens[ADDITIONAL_OPTIONS_SCREEN] = self.win.copy()

        pygame.draw.rect(self.win, WHITE, self.layouts.game_history_container)

        visible_history = []
        blit_sequence = []
        game_index = index
        # TODO: change slot design
        for slot in self.layouts.game_history_slots:
            try:
                _, winner, _ = game_history[game_index]
                visible_history.append(game_history[game_index])
            except IndexError:
                break
            if winner != "tie":
                text = self.texts["majorfont"].render(f"{winner} won", True, BLACK)
            else:
                text = self.texts["majorfont"].render("tie game", True, BLACK)
            blit_sequence.append((text, text.get_rect(center=slot.center)))
            game_index -= 1

        # draws lines to seperate each slot and blits the contents
        for slot in self.layouts.game_history_slots[1:5]:
            pygame.draw.line(self.win, BLACK, (slot.left+20, slot.top), (slot.right-20, slot.top))
        # blit the sequence and arrows
        self.win.blits(blit_sequence)
        up_arrow = pygame.draw.polygon(self.win, GREY, self.layouts.game_history_up_arrow)
        down_arrow = pygame.draw.polygon(self.win, GREY, self.layouts.game_history_down_arrow)
        pygame.display.update(self.layouts.game_history_container)

        return visible_history
        

class Layouts:
    """Object that holds Rects that organize game layout"""
    def __init__(self, win, texts):
        self.win, self.win_rect = win, win.get_rect()
        self.texts = texts
    
        self.past_game_slots, self.past_game_back_arrow = self.create_past_game_layout()
        # Rects for additional options screen
        self.additional_options_container, self.additional_options = self.create_additional_options_layout()
        # Rects for game history screen
        (self.game_history_container, self.game_history_slots, 
        self.game_history_up_arrow, self.game_history_down_arrow,
        self.game_history_up_arrow_rect, self.game_history_down_arrow_rect) = self.create_game_history_layout()

    def create_grid_layout(self, grid):
        """Setups the Rect for the grid image and creates the underlying Rects for X and O
        tiles to be placed"""
        # centers grid image to the top 80% of window
        center = self.win_rect.centerx, (self.win_rect.height * 0.8) // 2
        self.grid_rect = grid.get_rect(center=center)  

        # creates a list of Rects in the form of a grid that lie on top of the grid_rect
        # the indexes in the list will point to the Rect of a certain tile
        self.grid_tile_rects = []
        left = self.grid_rect.left
        top = self.grid_rect.top
        left_increment = self.grid_rect.width // 3
        top_increment = self.grid_rect.height // 3
        width, height = left_increment, top_increment
        for i in range(9):
            if i != 0 and i % 3 == 0:
                top += top_increment
                left = self.grid_rect.left
            # tile_rect_collide used so that user can click anywhere in the specific tile and their symbol will be placed
            tile_rect_collide = pygame.Rect(left, top, width, height)
            # tile_rect_pos used to make sure symbol appears in the middle of the tile
            tile_rect_pos = tile_rect_collide.inflate(-width*0.5, -height*0.5)  # makes rect 50% smaller
            left += left_increment
            self.grid_tile_rects.append((tile_rect_collide, tile_rect_pos))

    def create_game_info_layout(self, x_turn_tile, o_turn_tile):
        """Creates Rects all components of the bottom 20% of the game screen"""
        # Makes Rects for the X and O that indicate whose turn it is
        section = pygame.Rect(0, self.win_rect.height*(8/10), self.win_rect.width*(1/3), floor(self.win_rect.height*(2/10)))
        self.x_turn_tile_rect = x_turn_tile.get_rect(
            center=pygame.Rect(section.left, section.top, floor(section.width*(1/2)), section.height).center)
        self.o_turn_tile_rect = o_turn_tile.get_rect(
            center=pygame.Rect(floor(section.width*(1/2)), section.top, floor(section.width*(1/2)), section.height).center)

        # Makes Rects for turn count and small text above it
        section = pygame.Rect(floor(self.win_rect.width*(1/3)), floor(self.win_rect.height*(8/10)), floor(self.win_rect.width*(1/3)), floor(self.win_rect.height*(2/10)))
        self.turn_count_text_rect = pygame.Rect(section.left, section.top, section.width, floor(section.height*(3/10)))
        self.turn_count_rect = pygame.Rect(section.left, section.top+floor(section.height*(3/10)), section.width, floor(section.height*(7/10)))

    def create_game_history_layout(self):
        """Creates Rects for the game history screen"""
        x, y = floor(self.win_rect.width*(4/10)), floor(self.win_rect.height*(2/10))
        container = self.win_rect.inflate(-x, -y)

        height = floor(container.height*(1/5))
        slots = [
            pygame.Rect(container.left, container.top, container.width, height),
        ]
        # Splits container into five slots, start 1/5 of the way down. First slot already in list.
        for i in range(1,5):
            top = container.top + floor(container.height*(i/5))
            rect = pygame.Rect(container.left, top, container.width, height)
            slots.append(rect)

        # arrows for scrolling up and down the history
        i = scale(container, (-9/10))
        i.right, i.top = container.right, container.top
        up_arrow = [
            (i.left+floor(i.width*(1/4)), i.bottom),
            (i.left+floor(i.width*(1/4)), i.centery),
            (i.left, i.centery),
            (i.centerx, i.top),
            (i.right, i.centery),
            (i.right-floor(i.width*(1/4)), i.centery),
            (i.right-floor(i.width*(1/4)), i.bottom)
        ]
        j = i.copy()
        j.bottom = container.bottom
        down_arrow = [
            (j.left+floor(j.width*(1/4)), j.top),
            (j.left+floor(j.width*(1/4)), j.centery),
            (j.left, j.centery),
            (j.centerx, j.bottom),
            (j.right, j.centery),
            (j.right-floor(j.width*(1/4)), j.centery),
            (j.right-floor(j.width*(1/4)), j.top)
        ]

        return container, slots, up_arrow, down_arrow, i, j

    def create_additional_options_layout(self):
        """Creates Rects for the additional options screen"""
        options = []
        option_texts = [self.texts["history"], pygame.Surface((50,50)), pygame.Surface((50,50))]
        # Rect for white rectangular container surrounding the additional options
        x, y = floor(self.win_rect.width*(1/2)), floor(self.win_rect.height*(1/2))
        container_rect = self.win_rect.inflate(-x, -y)
        # splits the rectangular container into three horizontal Rects
        height = floor(container_rect.height*(1/3))
        for i in range(3):
            new_rect = container_rect.copy()
            new_rect.height = height
            if i != 0:
                new_rect.top += floor(container_rect.height*(i/3))
            else:
                pass
            options.append((option_texts[i], option_texts[i].get_rect(center=new_rect.center)))
        return container_rect, options

    def create_past_game_layout(self):
        """Creates the two small Rects on the bottom of the past game screen for holding the back button
        and some text. Will also create all coordinates for creating the back arrow"""
        section = pygame.Rect(self.win_rect.left, floor(self.win_rect.height*(8/10)), 
                              self.win_rect.width, floor(self.win_rect.height*(2/10)))
        slots = [
            pygame.Rect(section.left, section.top, floor(section.width*(2/10)), section.height),
            pygame.Rect(floor(section.width*(2/10)), section.top, floor(section.width*(8/10)), section.height)
        ]
        # back arrow coordinates will be inside the slots[0] Rect
        i = scale(slots[0], (-1/2))
        back_arrow = [
            (i.right, i.top+floor(i.height*(1/4))),
            (i.centerx, i.top+floor(i.height*(1/4))),
            (i.centerx, i.top),
            (i.left, i.top+floor(i.height*(1/2))),
            (i.centerx, i.bottom),
            (i.centerx, i.bottom-floor(i.height*(1/4))),
            (i.right, i.bottom-floor(i.height*(1/4)))
        ]
        return slots, back_arrow


class TTTFunc:
    """Handles the actual functionality of the game"""
    
    def __init__(self, visual: TTTVisual):
        # class that controls game ui
        self.visual = visual
        # game variables
        self.turn = None
        self.turn_count = 1
        self.grid = [None for _ in range(9)]
        self.game_history = []
        self.on_screen_game_history = None
        self.game_ongoing = False
        # variable to track what screen I am in
        self.cur_screen = START_SCREEN
        # index to scroll through game history
        self.game_history_index = -1

        self.mouse_click_handlers = {
            START_SCREEN: self.start_screen_clicked,
            GAME_SCREEN: self.game_screen_clicked,
            ADDITIONAL_OPTIONS_SCREEN: self.additional_options_screen_clicked,
            GAME_HISTORY_SCREEN: self.game_history_screen_clicked,
            PAST_GAME_SCREEN: self.past_game_screen_clicked,
        }

    def start_game(self):
        """Starts the game"""
        # randomly decides who goes first
        self.turn = choice('xo')
        # a game is now ongoing
        self.game_ongoing = True
        # show game screen on display
        self.visual.draw_game_screen(self.turn, self.turn_count)

    def mouse_clicked(self, pos):
        """When the mouse is clicked, this function uses current screen to search for the correct
        checks to do for that screen"""
        self.mouse_click_handlers[self.cur_screen](pos)

    def start_screen_clicked(self, pos):
        """Handles mouse click on the start screen"""
        if self.visual.play_button_rect.collidepoint(pos):
            self.start_game()
            self.cur_screen = GAME_SCREEN
    
    def game_screen_clicked(self, pos):
        """Handles mouse click on the game screen"""
        # if there is a game ongoing, check if a tile was clicked
        if self.game_ongoing:
            if index := self.is_tile_clicked(pos):
                index = int(index) 
                self.grid[index] = self.turn  # update grid
                self.visual.update_tile(index, self.turn)  # draw it on display
                # check for game over, if game not over, increment turn count
                if win_info := self.check_if_game_over():
                    self.game_over(win_info)
                    return
                self.turn_count += 1
                self.visual.update_turn_count(self.turn_count)
                # switch turns
                self.turn = "x" if self.turn != "x" else "o"  # toggle turn X -> O or O -> X
                self.visual.update_turn_tiles(self.turn)  # toggles transparency of two turn tiles
                return

        # check if the three dots 'more' button was clicked
        if self.visual.more_button_rect.collidepoint(pos):
            self.visual.draw_additional_options_screen()
            self.cur_screen = ADDITIONAL_OPTIONS_SCREEN

    def additional_options_screen_clicked(self, pos):
        """Handles mouse click on the additional options screen"""
        # Check if user even clicked on the menu, if not, go back to previous screen
        if self.visual.layouts.additional_options_container.collidepoint(pos):
            if self.visual.layouts.additional_options[0][1].collidepoint(pos):
                self.game_history_index = -1
                self.on_screen_game_history = self.visual.draw_game_history_screen(self.game_history, self.game_history_index)
                self.cur_screen = GAME_HISTORY_SCREEN
            elif self.visual.layouts.additional_options[1][1].collidepoint(pos):
                pass  # TODO: ACTUALLY DO SOMETHING HERE
            elif self.visual.layouts.additional_options[2][1].collidepoint(pos):
                pass  # TODO: ACTUALLY DO SOMETHING HERE
        else:
            self.visual.go_back_to_prev_screen(GAME_SCREEN)
            self.cur_screen = GAME_SCREEN

    def game_history_screen_clicked(self, pos):
        """Handles mouse click on the game history screen"""
        # first check if click was even inside container
        if self.visual.layouts.game_history_container.collidepoint(pos):
            # first check if either of the arrows were clicked
            if self.visual.layouts.game_history_down_arrow_rect.collidepoint(pos):
                self.game_history_index -= 1
                self.on_screen_game_history = self.visual.draw_game_history_screen(self.game_history, self.game_history_index)
            elif self.visual.layouts.game_history_up_arrow_rect.collidepoint(pos):
                if self.game_history_index < -1:
                    self.game_history_index += 1
                self.on_screen_game_history = self.visual.draw_game_history_screen(self.game_history, self.game_history_index)
            else:
                # go through all slots and see which one it was and get its index
                for i in range(len(self.visual.layouts.game_history_slots)):
                    # index will correspond to the correct entry in the list
                    if self.visual.layouts.game_history_slots[i].collidepoint(pos):
                        try:
                            game_data = self.on_screen_game_history[i]
                        except IndexError:
                            break
                        self.visual.draw_past_game_screen(game_data)
                        self.cur_screen = PAST_GAME_SCREEN
        else:
            self.visual.go_back_to_prev_screen(ADDITIONAL_OPTIONS_SCREEN)
            self.cur_screen = ADDITIONAL_OPTIONS_SCREEN

    def past_game_screen_clicked(self, pos):
        """Handles mouse click when there is a past game on the screen"""
        # One check getting a whole function might be a bit overkill, but whatever
        # this is the back button to go back to the game history screen
        if self.visual.layouts.past_game_slots[0].collidepoint(pos):
            self.visual.go_back_to_prev_screen(GAME_HISTORY_SCREEN)
            self.cur_screen = GAME_HISTORY_SCREEN

    def is_tile_clicked(self, pos):
        """Uses current mouse position and checks if a tile was clicked. Returns index of tile if
        tile was clicked"""
        for i in range(9):
            tile = self.visual.layouts.grid_tile_rects[i][0]
            if tile.collidepoint(pos):
                if self.grid[i] is not None:
                    return False
                # made into string so tile 0 (top left corner) doesn't evaluate to false in game.mouse_clicked()
                return str(i)  
        return False

    def check_if_game_over(self):
        """Goes through grid and checks all 8 possibilities to check if player won the game.
        Returns index of the tile at the middle of the winning row/col/dgnl and the index of the correct line
        direction to use according TTTVisual.o_lines and TTTVisual.x_lines"""
        # all the rows
        if self.turn == self.grid[0] == self.grid[1] == self.grid[2]:
            return 1, 1
        elif self.turn == self.grid[3] == self.grid[4] == self.grid[5]:
            return 4, 1
        elif self.turn == self.grid[6] == self.grid[7] == self.grid[8]:
            return 7, 1

        # all the columns
        if self.turn == self.grid[0] == self.grid[3] == self.grid[6]:
            return 3, 0
        elif self.turn == self.grid[1] == self.grid[4] == self.grid[7]:
            return 4, 0
        elif self.turn == self.grid[2] == self.grid[5] == self.grid[8]:
            return 5, 0

        # two diagonals
        if self.turn == self.grid[0] == self.grid[4] == self.grid[8]:
            return 4, 3
        elif self.turn == self.grid[2] == self.grid[4] == self.grid[6]:
            return 4, 2

        if self.turn_count == 9:
            return "tie"
        else:
            return False

    def game_over(self, win_info):
        """Called when a player wins. Draws the line to cross over the winning tiles and ends game"""
        self.game_ongoing = False
        # draws line to cross over winning tiles
        self.visual.draw_line(win_info, self.turn)
        # save current game into history as well as the winner and turn count, then reset grid
        if win_info != "tie":
            self.game_history.append((self.grid, self.turn, self.turn_count))
        else:
            self.game_history.append((self.grid, "tie", self.turn_count))
        self.grid = [None for x in range(9)]
        # reset game variables
        self.turn = None
        # update turn count text
        if win_info == "tie":
            self.visual.update_turn_count(None, tie=True)
        else:
            self.visual.update_turn_count(None, game_over=True)
        self.turn_count = 1
        self.visual.update_turn_tiles(self.turn)
        

def main():
    pygame.init()
    win = pygame.display.set_mode(WIN_SIZE)
    pygame.display.set_caption("TIC-TAC-TOE")
    # fonts for the game
    texts = create_texts()
    visual = TTTVisual(win, texts)
    game = TTTFunc(visual)

    visual.draw_start_screen()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            # check if tile is clicked
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    pos = event.pos
                    game.mouse_clicked(pos)
            elif event.type == KEYUP:
                if event.key == K_SPACE:
                    game.start_game()


def create_texts():
    """Renders text that is going to be used in the game and stores in dictionary, as well as the Font objects themselves"""
    # major font = 5% of window height | minor font = 3% of window height
    maj_font = load_font("arial", floor(WIN_HEIGHT*0.06))
    min_font = load_font("arial", floor(WIN_HEIGHT*0.03))
    texts = {
        "majorfont": maj_font,
        "minorfont": min_font,
        "currentturn": min_font.render("Current turn", True, BLACK),
        "gamewonin?turns": min_font.render("Game won in \u2193 turns", True, BLACK),
        "tiegame": maj_font.render("Tie Game", True, BLACK),
        "history": maj_font.render("History", True, BLACK),
        "play": maj_font.render("PLAY", True, BLACK),
    }
    return texts


def scale(rect: pygame.Rect, scale_factor) -> pygame.Rect:
    """Shrink or grows a Rect depending on the scale factor
    
    Paramaters:
        rect: pygame.Rect
        scale_factor: int or float that will be multiplied to rect.width and rect.height
                      and then the product will be added to the respective dimensions. To shrink,
                      scale_factor should be negative, to grow, positive
    Returns: pygame.Rect
    """
    x, y = floor(rect.width*scale_factor), floor(rect.height*scale_factor)
    return rect.inflate(x, y)


if __name__ == "__main__":
    main()
