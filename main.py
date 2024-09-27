import pygame
import sys
import random
import os
import asyncio  # Import asyncio

# Constants
SCALE_FACTOR = 1.5  # Increase the game size by this factor
TILE_SIZE = int(16 * SCALE_FACTOR)
WIDTH, HEIGHT = int(448 * SCALE_FACTOR), int(496 * SCALE_FACTOR)
FPS = 60
BLACK = (0, 0, 0)
GLOWING_YELLOW = (229, 255, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
FONT_SIZE = int(24 * SCALE_FACTOR)
POWER_PELLET_DURATION = FPS * 10  # Power mode lasts for 10 seconds
GAME_TIME = 90  # 90 seconds

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pac-Man")
clock = pygame.time.Clock()
font = pygame.font.Font(None, FONT_SIZE)

class Maze:
    def __init__(self, layout):
        self.layout = layout
        self.walls = []
        self.dots = []
        self.power_pellets = []
        self.junctions = []
        self.load_power_pellet_images()
        self.create_maze()
        # Removed background loading

    def load_power_pellet_images(self):
        self.pellet_images = []
        sports_balls_dir = "sports_balls"
        # Load all images from the 'sports_balls' directory
        for filename in os.listdir(sports_balls_dir):
            if filename.endswith('.png'):
                image = pygame.image.load(os.path.join(sports_balls_dir, filename)).convert_alpha()
                image = pygame.transform.scale(image, (int(12 * SCALE_FACTOR), int(12 * SCALE_FACTOR)))
                self.pellet_images.append(image)
        if not self.pellet_images:
            # If no images found, use a default circle
            default_image = pygame.Surface((int(12 * SCALE_FACTOR), int(12 * SCALE_FACTOR)), pygame.SRCALPHA)
            pygame.draw.circle(default_image, WHITE, (int(6 * SCALE_FACTOR), int(6 * SCALE_FACTOR)), int(6 * SCALE_FACTOR))
            self.pellet_images.append(default_image)

    def create_maze(self):
        maze_width = len(self.layout[0])
        maze_height = len(self.layout)
        for y, row in enumerate(self.layout):
            for x, col in enumerate(row):
                if col == '#':
                    self.walls.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                elif col == '.':
                    self.dots.append(pygame.Rect(x * TILE_SIZE + int(6 * SCALE_FACTOR), y * TILE_SIZE + int(6 * SCALE_FACTOR), int(4 * SCALE_FACTOR), int(4 * SCALE_FACTOR)))
                elif col == 'o':
                    pellet_rect = pygame.Rect(x * TILE_SIZE + int(2 * SCALE_FACTOR), y * TILE_SIZE + int(2 * SCALE_FACTOR), int(12 * SCALE_FACTOR), int(12 * SCALE_FACTOR))
                    image = random.choice(self.pellet_images)
                    self.power_pellets.append({'rect': pellet_rect, 'image': image})

        # Identify junctions
        self.identify_junctions()

    def identify_junctions(self):
        maze_width = len(self.layout[0])
        maze_height = len(self.layout)
        for y in range(maze_height):
            for x in range(maze_width):
                if self.layout[y][x] != '#':
                    directions = 0
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < maze_width and 0 <= ny < maze_height:
                            if self.layout[ny][nx] != '#':
                                directions += 1
                    if directions >= 3:
                        self.junctions.append((x * TILE_SIZE, y * TILE_SIZE))

    def is_junction(self, rect):
        return (rect.x, rect.y) in self.junctions

    def draw(self, surface):
        # Fill the background with black
        surface.fill(BLACK)
        for wall in self.walls:
            pygame.draw.rect(surface, GLOWING_YELLOW, (wall.x + int(2 * SCALE_FACTOR), wall.y + int(2 * SCALE_FACTOR), TILE_SIZE - int(4 * SCALE_FACTOR), TILE_SIZE - int(4 * SCALE_FACTOR)))

        for dot in self.dots:
            pygame.draw.rect(surface, WHITE, dot)

        for pellet in self.power_pellets:
            surface.blit(pellet['image'], pellet['rect'])

class PacMan:
    def __init__(self, position):
        self.image = pygame.image.load("WSC SPORTS_Logo_03_White.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=position)
        self.direction = pygame.Vector2(0, 0)
        self.next_direction = pygame.Vector2(0, 0)
        self.speed = 2 * SCALE_FACTOR
        self.score = 0
        self.lives = 3
        self.power_mode = False
        self.power_timer = 0
        self.has_moved = False  # Track if the player has made a move

    def update(self, maze):
        self.handle_input()
        self.move(maze)
        self.check_collisions(maze)
        self.update_power_mode()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.next_direction = pygame.Vector2(-1, 0)
            self.has_moved = True
        elif keys[pygame.K_RIGHT]:
            self.next_direction = pygame.Vector2(1, 0)
            self.has_moved = True
        elif keys[pygame.K_UP]:
            self.next_direction = pygame.Vector2(0, -1)
            self.has_moved = True
        elif keys[pygame.K_DOWN]:
            self.next_direction = pygame.Vector2(0, 1)
            self.has_moved = True

    def move(self, maze):
        # Try to turn if possible
        if self.can_move(self.next_direction, maze):
            self.direction = self.next_direction
        # Move in current direction if possible
        if self.can_move(self.direction, maze):
            self.rect.move_ip(self.direction.x * self.speed, self.direction.y * self.speed)

    def can_move(self, direction, maze):
        new_rect = self.rect.move(direction.x * self.speed, direction.y * self.speed)
        return not any(new_rect.colliderect(wall) for wall in maze.walls)

    def check_collisions(self, maze):
        # Collect dots
        for dot in maze.dots[:]:
            if self.rect.colliderect(dot):
                maze.dots.remove(dot)
                self.score += 10
        # Collect power pellets
        for pellet in maze.power_pellets[:]:
            if self.rect.colliderect(pellet['rect']):
                maze.power_pellets.remove(pellet)
                self.score += 50
                self.power_mode = True
                self.power_timer = POWER_PELLET_DURATION

    def update_power_mode(self):
        if self.power_mode:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.power_mode = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Ghost:
    def __init__(self, position, color):
        self.start_pos = position
        self.color = color
        self.image = self.create_ghost_image()
        self.rect = self.image.get_rect(topleft=position)
        self.direction = pygame.Vector2(0, 0)
        self.previous_direction = self.direction
        self.speed = 2 * SCALE_FACTOR
        self.visible = True
        self.blink_timer = 0
        self.power_mode = False

    def create_ghost_image(self, full_circle=False):
        image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if full_circle:
            pygame.draw.circle(image, self.color, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2)
            if self.color == BLACK:
                pygame.draw.circle(image, WHITE, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2, int(2 * SCALE_FACTOR))
        else:
            pygame.draw.circle(image, self.color, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2, int(2 * SCALE_FACTOR))
            if self.color == BLACK:
                pygame.draw.circle(image, WHITE, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2, int(2 * SCALE_FACTOR))
                pygame.draw.circle(image, BLACK, (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2 - int(2 * SCALE_FACTOR), int(2 * SCALE_FACTOR))
        return image

    def update(self, maze, power_mode, player_moved):
        self.power_mode = power_mode
        if player_moved:
            self.move(maze)
        self.handle_blinking()

    def move(self, maze):
        # Mark previous movement as x
        x = self.direction

        # Calculate optional movements that do not collide with walls
        possible_directions = []
        for direction in [pygame.Vector2(1, 0), pygame.Vector2(-1, 0), pygame.Vector2(0, 1), pygame.Vector2(0, -1)]:
            new_rect = self.rect.move(direction.x * self.speed, direction.y * self.speed)
            if not any(new_rect.colliderect(wall) for wall in maze.walls):
                possible_directions.append(direction)

        if not possible_directions:
            # If no possible movements, stay in place
            self.direction = pygame.Vector2(0, 0)
            return

        # Check if at a junction
        at_junction = maze.is_junction(self.rect)

        if at_junction:
            # At junction, with 70% probability, keep moving in same direction if possible
            if x in possible_directions and random.random() < 0.7:
                self.direction = x
            else:
                # Choose other legal directions uniformly
                other_directions = [d for d in possible_directions if d != x]
                if other_directions:
                    self.direction = random.choice(other_directions)
                else:
                    self.direction = x
        else:
            # Decide on next movement
            if x in possible_directions and random.random() < 0.99:
                # Keep moving in the same direction with 99% probability
                self.direction = x
            else:
                # Choose a new direction
                self.direction = random.choice(possible_directions)

        # Move in the chosen direction
        self.rect.move_ip(self.direction.x * self.speed, self.direction.y * self.speed)

        # Update previous direction
        self.previous_direction = self.direction

    def handle_blinking(self):
        if self.power_mode:
            self.blink_timer = (self.blink_timer + 1) % 30  # Adjust blink speed here
            self.visible = self.blink_timer < 15  # Visible for half the time
            # Change to full circle shape
            self.image = self.create_ghost_image(full_circle=True)
        else:
            self.visible = True
            # Reset to ring shape
            self.image = self.create_ghost_image(full_circle=False)

    def draw(self, surface):
        if self.visible:
            surface.blit(self.image, self.rect)

    def reset_position(self):
        self.rect.topleft = self.start_pos
        self.direction = pygame.Vector2(0, 0)

class Game:
    def __init__(self):
        self.maze = Maze(self.load_maze())
        self.pacman = PacMan((13 * TILE_SIZE, 23 * TILE_SIZE))
        self.ghosts = self.create_ghosts()
        self.running = True
        self.state = 'playing'  # Can be 'playing', 'game_over', 'won'
        self.start_time = None  # Will be set after first move
        self.time_left = GAME_TIME
        self.load_buttom_image()  # Load the 'buttom.png' image

    def load_buttom_image(self):
        # Load and scale the buttom image
        self.buttom_image = pygame.image.load("buttom.png").convert_alpha()
        self.buttom_image = pygame.transform.scale(self.buttom_image, (WIDTH, int(50 * SCALE_FACTOR)))
        self.buttom_rect = self.buttom_image.get_rect(midbottom=(WIDTH // 2, HEIGHT))

    def load_maze(self):
        maze_layout = [
            "############################",
            "#o...........##...........o#",
            "#.####.#####.##.#####.####.#",
            "#.####.#####.##.#####.####.#",
            "#..........................#",
            "#.####.##.########.##.####.#",
            "#......##....##....##......#",
            "######.##### ## #####.######",
            "     #.##### ## #####.#     ",
            "     #.##          ##.#     ",
            "     #.## ##----## ##.#     ",
            "######.## #      # ##.######",
            "#     .   #      #   .     #",
            "######.## ###--### ##.######",
            "     #.##          ##.#     ",
            "     #.## ######## ##.#     ",
            "######.## ######## ##.######",
            "#............##............#",
            "#.####.#####.##.#####.####.#",
            "#...##....o.........#....#.#",
            "###.##.##.########.##.##.###",
            "#......##....##....##......#",
            "#.##########.##.##########.#",
            "#o........................o#",
            "############################",
        ]
        return maze_layout

    def create_ghosts(self):
        ghost_colors = [
            BLUE,
            BLACK,
            RED,
            YELLOW,
            GREEN
        ]
        # Position ghosts inside the ghost box on lines 12-13 (indices 11-12)
        base_y = 11 * TILE_SIZE
        base_x = 13 * TILE_SIZE  # Center x position

        ghost_positions = [
            (base_x - TILE_SIZE, base_y),          # Left position
            (base_x, base_y),                      # Center position
            (base_x + TILE_SIZE, base_y),          # Right position
            (base_x - TILE_SIZE // 2, base_y + TILE_SIZE),  # Bottom left
            (base_x + TILE_SIZE // 2, base_y + TILE_SIZE),  # Bottom right
        ]
        ghosts = []
        for pos, color in zip(ghost_positions, ghost_colors):
            ghost = Ghost(pos, color)
            # Ensure ghosts are not inside walls
            if not any(ghost.rect.colliderect(wall) for wall in self.maze.walls):
                ghosts.append(ghost)
            else:
                # Adjust position if colliding
                ghost.rect.topleft = self.find_valid_position()
                ghosts.append(ghost)
        return ghosts

    def find_valid_position(self):
        # Find a valid position inside the ghost box
        x = 12 * TILE_SIZE
        y = 11 * TILE_SIZE
        while True:
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            if not any(rect.colliderect(wall) for wall in self.maze.walls):
                return (x, y)
            x += TILE_SIZE
            if x > (15 * TILE_SIZE):
                x = 12 * TILE_SIZE
                y += TILE_SIZE

    def check_collisions(self):
        for ghost in self.ghosts:
            if self.pacman.rect.colliderect(ghost.rect):
                if self.pacman.power_mode:
                    ghost.reset_position()
                    self.pacman.score += 200
                else:
                    self.pacman.lives -= 1
                    if self.pacman.lives <= 0:
                        self.state = 'game_over'
                    else:
                        self.reset_positions()

        # Check for win condition
        if not self.maze.dots and not self.maze.power_pellets:
            self.state = 'won'

    def reset_positions(self):
        self.pacman.rect.topleft = (13 * TILE_SIZE, 23 * TILE_SIZE)
        self.pacman.direction = pygame.Vector2(0, 0)
        self.pacman.next_direction = pygame.Vector2(0, 0)
        self.pacman.has_moved = False
        for ghost in self.ghosts:
            ghost.reset_position()

    def reset_game(self):
        self.maze = Maze(self.load_maze())
        self.pacman = PacMan((13 * TILE_SIZE, 23 * TILE_SIZE))
        self.ghosts = self.create_ghosts()
        self.state = 'playing'
        self.start_time = None
        self.time_left = GAME_TIME
        self.load_buttom_image()

    # def run(self):
    #     while self.running:
    #         self.handle_events()
    #         if self.state == 'playing':
    #             self.update()
    #             self.draw()
    #         elif self.state == 'game_over':
    #             self.show_game_over_screen()
    #         elif self.state == 'won':
    #             self.show_win_screen()
    #         pygame.display.flip()
    #         clock.tick(FPS)
    #
    #     pygame.quit()
    #     sys.exit()

    def handle_events(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_c]) and \
           (keys[pygame.K_w] and keys[pygame.K_s] and keys[pygame.K_c]):
            self.state = 'won'
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state == 'game_over' and event.type == pygame.MOUSEBUTTONDOWN:
                if self.retry_button.collidepoint(event.pos):
                    self.reset_game()
            elif self.state == 'won' and event.type == pygame.MOUSEBUTTONDOWN:
                if self.link_rect.collidepoint(event.pos):
                    import webbrowser
                    webbrowser.open("https://wsc-sports.com/careers/?coref=1.10.r7E_21D&t=1727432954943")

    def update(self):
        self.pacman.update(self.maze)
        self.pacman.update_power_mode()
        player_moved = self.pacman.has_moved

        if player_moved and self.start_time is None:
            self.start_time = pygame.time.get_ticks()

        for ghost in self.ghosts:
            ghost.update(self.maze, self.pacman.power_mode, player_moved)
        self.check_collisions()
        # Update timer
        if self.start_time:
            elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000
            self.time_left = max(0, GAME_TIME - int(elapsed_time))
            if self.time_left <= 0:
                self.state = 'game_over'

    def draw(self):
        # Fill the background with black
        screen.fill(BLACK)
        self.maze.draw(screen)
        self.pacman.draw(screen)
        for ghost in self.ghosts:
            ghost.draw(screen)
        self.draw_score()
        self.draw_lives()
        self.draw_timer()
        # Draw the buttom image
        screen.blit(self.buttom_image, self.buttom_rect)

    def draw_score(self):
        score_text = font.render(f"Score: {self.pacman.score}", True, WHITE)
        screen.blit(score_text, (int(10 * SCALE_FACTOR), HEIGHT - FONT_SIZE - int(55 * SCALE_FACTOR)))

    def draw_lives(self):
        lives_text = font.render(f"Lives: {self.pacman.lives}", True, WHITE)
        screen.blit(lives_text, (WIDTH - int(100 * SCALE_FACTOR), HEIGHT - FONT_SIZE - int(55 * SCALE_FACTOR)))

    def draw_timer(self):
        if self.start_time:
            minutes = self.time_left // 60
            seconds = self.time_left % 60
            timer_text = font.render(f"Time: {minutes}:{seconds:02}", True, WHITE)
        else:
            minutes = GAME_TIME // 60
            seconds = GAME_TIME % 60
            timer_text = font.render(f"Time: {minutes}:{seconds:02}", True, WHITE)
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, HEIGHT - FONT_SIZE - int(55 * SCALE_FACTOR)))

    def show_game_over_screen(self):
        screen.fill(BLACK)
        game_over_text = font.render("Game Over", True, WHITE)
        retry_text = font.render("Retry", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - int(50 * SCALE_FACTOR)))
        self.retry_button = retry_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        pygame.draw.rect(screen, GLOWING_YELLOW, self.retry_button.inflate(int(20 * SCALE_FACTOR), int(10 * SCALE_FACTOR)), border_radius=5)
        screen.blit(retry_text, self.retry_button)

    def show_win_screen(self):
        screen.fill(BLACK)
        win_text = font.render("You Won!", True, WHITE)
        message_text = font.render("WSC Sports is Hiring - Click Here", True, GLOWING_YELLOW)
        screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - int(50 * SCALE_FACTOR)))
        self.link_rect = message_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(message_text, self.link_rect)

    async def run(self):
        while self.running:
            self.handle_events()
            if self.state == 'playing':
                self.update()
                self.draw()
            elif self.state == 'game_over':
                self.show_game_over_screen()
            elif self.state == 'won':
                self.show_win_screen()
            pygame.display.flip()
            await asyncio.sleep(0)  # Yield to the event loop
            clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())
